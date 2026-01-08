from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class OrderBook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    last_update_id: int
    bids: str
    asks: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
