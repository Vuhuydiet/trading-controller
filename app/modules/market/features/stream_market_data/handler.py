import json
from typing import Callable
from app.modules.market.infrastructure.binance_ws_client import BinanceWebSocketClient


class StreamMarketDataHandler:
    def __init__(self):
        self.ws_client = BinanceWebSocketClient()

    async def stream_klines(self, symbol: str, interval: str, callback: Callable):
        stream = self.ws_client.get_kline_stream(symbol, interval)
        await self.ws_client.connect(stream, callback)

    async def stream_ticker(self, symbol: str, callback: Callable):
        stream = self.ws_client.get_ticker_stream(symbol)
        await self.ws_client.connect(stream, callback)

    async def stream_trades(self, symbol: str, callback: Callable):
        stream = self.ws_client.get_trade_stream(symbol)
        await self.ws_client.connect(stream, callback)

    async def stream_depth(self, symbol: str, callback: Callable):
        stream = self.ws_client.get_depth_stream(symbol)
        await self.ws_client.connect(stream, callback)

    async def stream_combined(self, streams: list[str], callback: Callable):
        await self.ws_client.connect_combined(streams, callback)

    async def disconnect(self):
        await self.ws_client.disconnect()
