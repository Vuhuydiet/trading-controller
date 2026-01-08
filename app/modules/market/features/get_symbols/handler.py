from typing import List, Optional
from app.modules.market.infrastructure.symbols_cache import get_symbols_cache
from .dtos import SymbolResponse, SymbolDetailResponse, SymbolInfoResponse


class GetSymbolsHandler:
    def __init__(self):
        self.symbols_cache = get_symbols_cache()

    async def handle(
        self,
        quote_asset: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SymbolResponse]:
        symbols = await self.symbols_cache.get_all_symbols()

        filtered_symbols = symbols
        if quote_asset:
            filtered_symbols = [s for s in filtered_symbols if s.get("quoteAsset") == quote_asset.upper()]
        if status:
            filtered_symbols = [s for s in filtered_symbols if s.get("status") == status.upper()]

        result = []
        for symbol_data in filtered_symbols:
            result.append(SymbolResponse(
                symbol=symbol_data.get("symbol"),
                base_asset=symbol_data.get("baseAsset"),
                quote_asset=symbol_data.get("quoteAsset"),
                status=symbol_data.get("status"),
                price_precision=symbol_data.get("quotePrecision", 0),
                quantity_precision=symbol_data.get("baseAssetPrecision", 0)
            ))

        return result


class GetSymbolDetailHandler:
    def __init__(self):
        self.symbols_cache = get_symbols_cache()

    async def handle(self, symbol: str) -> SymbolDetailResponse:
        symbol_data = await self.symbols_cache.get_symbol(symbol.upper())

        if not symbol_data:
            raise ValueError(f"Symbol {symbol} not found")

        return SymbolDetailResponse(
            symbol=symbol_data.get("symbol"),
            base_asset=symbol_data.get("baseAsset"),
            quote_asset=symbol_data.get("quoteAsset"),
            status=symbol_data.get("status"),
            price_precision=symbol_data.get("quotePrecision", 0),
            quantity_precision=symbol_data.get("baseAssetPrecision", 0),
            base_asset_precision=symbol_data.get("baseAssetPrecision", 0),
            quote_asset_precision=symbol_data.get("quotePrecision", 0),
            order_types=symbol_data.get("orderTypes", []),
            is_spot_trading_allowed=symbol_data.get("isSpotTradingAllowed", False),
            is_margin_trading_allowed=symbol_data.get("isMarginTradingAllowed", False),
            permissions=symbol_data.get("permissions", [])
        )


class GetSymbolInfoHandler:
    def __init__(self):
        self.symbols_cache = get_symbols_cache()

    async def handle(self, symbol: str) -> SymbolInfoResponse:
        symbol_data = await self.symbols_cache.get_symbol(symbol.upper())

        if not symbol_data:
            raise ValueError(f"Symbol {symbol} not found")

        return SymbolInfoResponse(
            symbol=symbol_data.get("symbol"),
            base_asset=symbol_data.get("baseAsset"),
            quote_asset=symbol_data.get("quoteAsset"),
            status=symbol_data.get("status"),
            price_precision=symbol_data.get("quotePrecision", 0),
            quantity_precision=symbol_data.get("baseAssetPrecision", 0),
            base_asset_precision=symbol_data.get("baseAssetPrecision", 0),
            quote_asset_precision=symbol_data.get("quotePrecision", 0),
            order_types=symbol_data.get("orderTypes", []),
            is_spot_trading_allowed=symbol_data.get("isSpotTradingAllowed", False),
            is_margin_trading_allowed=symbol_data.get("isMarginTradingAllowed", False),
            permissions=symbol_data.get("permissions", []),
            filters=symbol_data.get("filters", [])
        )
