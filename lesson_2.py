"""
Stage 2: Giving the AI "Hands" (Tool Calling / Function Calling)
----------------------------------------------------------------
This script teaches you how to give an AI model custom Python functions.
When the user asks something that requires live data or calculations,
the AI will automatically call our Python function to get the real answer!
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY missing from .env")
    exit(1)

client = genai.Client(api_key=api_key)

# -------------------------------------------------------------
# STEP 1: Define normal Python functions (Tools)
# Notice: The docstring is CRUCIAL. The AI reads your docstring
# to decide WHEN and HOW to use the tool!
# -------------------------------------------------------------

def check_warehouse_inventory(item_name: str) -> str:
    """
    Check the current stock quantity and price of an item in the warehouse inventory.
    Args:
        item_name: The name of the item to search (e.g. 'laptop', 'headphones', 'keyboard')
    """
    print(f"\n⚙️ [TOOL TRIGGERED]: Running check_warehouse_inventory(item_name='{item_name}') in Python...")
    
    # Simulate a real database lookup:
    inventory = {
        "laptop": {"stock": 3, "price": 1200.0},
        "headphones": {"stock": 0, "price": 150.0},
        "keyboard": {"stock": 14, "price": 75.0}
    }
    
    item = inventory.get(item_name.lower())
    if not item:
        return f"Item '{item_name}' was not found in the warehouse database."
    
    if item["stock"] == 0:
        return f"Status: OUT OF STOCK. Item: {item_name}, Price: ${item['price']:.2f}."
    
    return f"Status: IN STOCK. Item: {item_name}, Quantity Available: {item['stock']}, Price: ${item['price']:.2f}."


def calculate_discount(original_price: float, discount_percent: float) -> str:
    """
    Calculate the discounted price given the original price and discount percentage.
    Args:
        original_price: The standard price of the item before discount.
        discount_percent: The percentage discount to apply (e.g. 20 for 20% off).
    """
    print(f"\n⚙️ [TOOL TRIGGERED]: Running calculate_discount(original_price={original_price}, discount_percent={discount_percent}) in Python...")
    
    discount_amount = original_price * (discount_percent / 100.0)
    final_price = original_price - discount_amount
    return f"Original: ${original_price:.2f}, Discount: {discount_percent}%, Final Price: ${final_price:.2f}"


# -------------------------------------------------------------
# STEP 2: Give the tools to the AI in client.chats.create
# -------------------------------------------------------------
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        # We pass our Python functions directly in the tools list!
        tools=[check_warehouse_inventory, calculate_discount],
        # System instructions to guide behavior
        system_instruction="You are a helpful warehouse customer support assistant. Always use tools to verify real stock and calculate discounts."
    )
)

# -------------------------------------------------------------
# STEP 3: Ask a question that requires BOTH tools!
# -------------------------------------------------------------
user_query = "Do we have any laptops in stock? If so, how much would one cost with a 15% student discount?"

print(f"👤 User Question: '{user_query}'\n")
print("🤖 Sending to Gemini (it will figure out which tools to run)...")

response = chat.send_message(user_query)

print("\n" + "=" * 60)
print("🤖 FINAL AI ANSWER TO USER:")
print("=" * 60)
print(response.text)
print("=" * 60)
