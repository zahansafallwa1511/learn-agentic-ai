"""
Stage 1: Real API Call with Free Gemini API & Pydantic Structured Outputs
-------------------------------------------------------------------------
This script connects to Google's fast, free Gemini 3.5 Flash Lite model
and forces it to return typed data matching our exact Pydantic schema.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

# 1. Load your API key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key in ["your_api_key_here", "PASTE_YOUR_KEY_HERE"]:
    print("❌ ERROR: Missing GEMINI_API_KEY!")
    print("\n👉 Follow these 2 steps to get a free key:")
    print("1. Go to: https://aistudio.google.com/apikey (sign in with your Google account)")
    print("2. Click 'Create API key' and paste it into a .env file in this directory:")
    print('   GEMINI_API_KEY="AIzaSy..."')
    exit(1)

from google import genai
from google.genai import types

# 2. Define the Pydantic data structure
class ExpenseItem(BaseModel):
    name: str = Field(description="Name of item purchased")
    price: float = Field(description="Price as a float number")

class ReceiptData(BaseModel):
    store_name: str = Field(description="Merchant or store name")
    date: str = Field(description="Date in YYYY-MM-DD format if known")
    items: List[ExpenseItem] = Field(description="List of purchased items")
    total: float = Field(description="Total price paid")

# 3. Initialize the Google GenAI Client
client = genai.Client(api_key=api_key)

# 4. Messy, unformatted text
user_prompt = """
Yo! just went for lunch at taj restaurant and had a chicken khichuri for 20 dollars and a mango lassi for 5 dollars. It was on 2023-08-15.
"""

print("🚀 Sending messy receipt text to Gemini Flash Lite...")

# 5. Use client.chats.create with structured output configuration
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReceiptData,
    ),
)

response = chat.send_message(user_prompt)

# 6. Validate and turn into a native Python object
receipt: ReceiptData = ReceiptData.model_validate_json(response.text)

print("\n✅ SUCCESS! Clean Python object received:")
print(f"Merchant : {receipt.store_name}")
print(f"Date     : {receipt.date}")
print(f"Total    : ${receipt.total:.2f}")
print("Items:")
for item in receipt.items:
    print(f"  • {item.name}: ${item.price:.2f}")
