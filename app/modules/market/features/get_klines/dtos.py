from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

VALID_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]


class KlineRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    interval: str = Field(..., description="Kline interval (e.g., 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)")
    start_time: Optional[int] = Field(None, description="Start time in milliseconds")
    end_time: Optional[int] = Field(None, description="End time in milliseconds")
    limit: int = Field(500, ge=1, le=1000, description="Number of klines to return")

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, v: str) -> str:
        if v not in VALID_INTERVALS:
            raise ValueError(f"Invalid interval. Must be one of: {', '.join(VALID_INTERVALS)}")
        return v


class KlineResponse(BaseModel):
    symbol: str
    interval: str
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: datetime

    class Config:
        from_attributes = True
