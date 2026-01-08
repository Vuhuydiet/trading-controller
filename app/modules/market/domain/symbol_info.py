from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class SymbolInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True)
    base_asset: str = Field(index=True)
    quote_asset: str = Field(index=True)
    status: str = Field(index=True)
    price_precision: int
    quantity_precision: int
    base_asset_precision: int
    quote_asset_precision: int
    order_types: str
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    permissions: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
