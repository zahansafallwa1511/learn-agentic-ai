"""
Stage 1: Structured Data Extraction with Pydantic
-------------------------------------------------
This demonstrates how an AI Developer extracts clean, typed data
from messy human text.
"""

from pydantic import BaseModel, Field
from typing import List
import json

class Item(BaseModel):
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item in USD")


class Order(BaseModel):
    order_id: str = Field(..., description="The unique identifier for the order")
    items: List[Item] = Field(..., description="A list of items in the order")
    total: float = Field(..., description="The total price of the order in USD")