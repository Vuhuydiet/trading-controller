from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class Kline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    interval: str = Field(index=True)
    open_time: datetime = Field(index=True)
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
