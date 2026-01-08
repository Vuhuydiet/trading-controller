from pydantic import BaseModel, Field
from typing import Optional, List


class SymbolResponse(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    price_precision: int
    quantity_precision: int

    class Config:
        from_attributes = True


class SymbolDetailResponse(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    price_precision: int
    quantity_precision: int
    base_asset_precision: int
    quote_asset_precision: int
    order_types: List[str]
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    permissions: List[str]

    class Config:
        from_attributes = True


class SymbolInfoResponse(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    price_precision: int
    quantity_precision: int
    base_asset_precision: int
    quote_asset_precision: int
    order_types: List[str]
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    permissions: List[str]
    filters: List[dict]

    class Config:
        from_attributes = True
