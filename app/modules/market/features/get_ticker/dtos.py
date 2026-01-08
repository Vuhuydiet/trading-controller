from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class TickerResponse(BaseModel):
    symbol: str
    price_change: Decimal
    price_change_percent: Decimal
    weighted_avg_price: Decimal
    prev_close_price: Decimal
    last_price: Decimal
    last_qty: Decimal
    bid_price: Decimal
    bid_qty: Decimal
    ask_price: Decimal
    ask_qty: Decimal
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    open_time: datetime
    close_time: datetime
    first_id: int
    last_id: int
    count: int
    timestamp: datetime = None

    class Config:
        from_attributes = True


class TickersResponse(BaseModel):
    tickers: list[TickerResponse]
    timestamp: datetime
