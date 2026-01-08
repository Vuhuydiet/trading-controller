from decimal import Decimal
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from .dtos import DepthResponse, OrderBookEntry, VALID_LIMITS


class GetDepthHandler:
    def __init__(self):
        self.binance_client = BinanceRestClient()

    async def handle(self, symbol: str, limit: int = 100) -> DepthResponse:
        symbol_upper = symbol.upper()

        if limit not in VALID_LIMITS:
            raise ValueError(f"Invalid limit. Must be one of: {', '.join(map(str, VALID_LIMITS))}")

        raw_depth = await self.binance_client.get_order_book(symbol_upper, limit)

        bids = []
        for bid in raw_depth.get("bids", []):
            bids.append(OrderBookEntry(
                price=Decimal(bid[0]),
                quantity=Decimal(bid[1])
            ))

        asks = []
        for ask in raw_depth.get("asks", []):
            asks.append(OrderBookEntry(
                price=Decimal(ask[0]),
                quantity=Decimal(ask[1])
            ))

        return DepthResponse(
            symbol=symbol_upper,
            last_update_id=raw_depth.get("lastUpdateId", 0),
            bids=bids,
            asks=asks
        )
