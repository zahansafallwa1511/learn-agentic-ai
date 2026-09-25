"""
Lesson 1: Structured Data Extraction with Pydantic & Gemini API
---------------------------------------------------------------
This lesson demonstrates how to connect to Gemini 3.5 Flash Lite
and force it to return typed data matching a strict Pydantic schema.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from google import genai
from google.genai import types

# 1. Load API Key from local .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY missing from .env")
    exit(1)

client = genai.Client(api_key=api_key)

# 2. Define the Pydantic schema
class ExpenseItem(BaseModel):
    name: str = Field(description="Name of item purchased")
    price: float = Field(description="Price as a float number")

class ReceiptData(BaseModel):
    store_name: str = Field(description="Merchant or store name")
    date: str = Field(description="Date in YYYY-MM-DD format if known")
    items: List[ExpenseItem] = Field(description="List of purchased items")
    total: float = Field(description="Total price paid")

# 3. Messy human text
user_prompt = """
Yo! Just grabbed lunch at Chipotle on 2026-09-24.
I got a Chicken Burrito Bowl for 11.25, added Chips & Guac for 4.50,
and a bottle of sparkling water for 2.95.
With taxes it came out to exactly 18.70.
"""

# 4. Enforce structured output via chat API
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReceiptData,
    ),
)

response = chat.send_message(user_prompt)

# 5. Turn into typed Python object
receipt: ReceiptData = ReceiptData.model_validate_json(response.text)

print("✅ SUCCESS! Clean Python object received:")
print(f"Merchant : {receipt.store_name}")
print(f"Date     : {receipt.date}")
print(f"Total    : ${receipt.total:.2f}")
print("Items:")
for item in receipt.items:
    print(f"  • {item.name}: ${item.price:.2f}")