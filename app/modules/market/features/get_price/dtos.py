from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class PriceResponse(BaseModel):
    symbol: str
    price: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True


class PricesResponse(BaseModel):
    prices: list[PriceResponse]
    timestamp: datetime
