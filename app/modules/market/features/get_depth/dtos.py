from pydantic import BaseModel, Field, field_validator
from typing import List
from decimal import Decimal

VALID_LIMITS = [5, 10, 20, 50, 100]


class OrderBookEntry(BaseModel):
    price: Decimal
    quantity: Decimal


class DepthResponse(BaseModel):
    symbol: str
    last_update_id: int
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]

    class Config:
        from_attributes = True
