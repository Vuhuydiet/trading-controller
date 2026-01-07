import json
import asyncio
from typing import Callable, Optional, Set
from websockets import connect, WebSocketClientProtocol
from app.shared.core.config import settings


class BinanceWebSocketClient:
    def __init__(self):
        self.base_url = settings.BINANCE_WS_BASE_URL
        self.ws: Optional[WebSocketClientProtocol] = None
        self.subscriptions: Set[str] = set()
        self.running = False
        self.callback: Optional[Callable] = None

    async def connect(self, stream: str, callback: Callable):
        self.callback = callback
        self.running = True

        url = f"{self.base_url}/ws/{stream}"

        try:
            async with connect(url) as websocket:
                self.ws = websocket
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        if self.callback:
                            await self.callback(data)
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        break
        except Exception as e:
            self.running = False
            raise

    async def connect_combined(self, streams: list[str], callback: Callable):
        self.callback = callback
        self.running = True

        combined_stream = "/".join(streams)
        url = f"{self.base_url}/stream?streams={combined_stream}"

        try:
            async with connect(url) as websocket:
                self.ws = websocket
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        if self.callback:
                            await self.callback(data)
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        break
        except Exception as e:
            self.running = False
            raise

    async def disconnect(self):
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None

    @staticmethod
    def get_kline_stream(symbol: str, interval: str) -> str:
        return f"{symbol.lower()}@kline_{interval}"

    @staticmethod
    def get_ticker_stream(symbol: str) -> str:
        return f"{symbol.lower()}@ticker"

    @staticmethod
    def get_trade_stream(symbol: str) -> str:
        return f"{symbol.lower()}@trade"

    @staticmethod
    def get_depth_stream(symbol: str, level: Optional[int] = None) -> str:
        if level:
            return f"{symbol.lower()}@depth{level}"
        return f"{symbol.lower()}@depth"

    @staticmethod
    def get_book_ticker_stream(symbol: str) -> str:
        return f"{symbol.lower()}@bookTicker"
