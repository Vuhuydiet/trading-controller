import asyncio
import json
from typing import Optional, Set, Callable
from datetime import datetime
from decimal import Decimal
from websockets import connect, WebSocketClientProtocol, ConnectionClosed
from app.shared.core.config import settings
from app.modules.market.infrastructure.price_cache import get_price_cache
from app.shared.core.logging_config import get_logger

logger = get_logger(__name__)


class BinanceWebSocketManager:
    def __init__(self):
        self.base_url = settings.BINANCE_WS_BASE_URL
        self.ws: Optional[WebSocketClientProtocol] = None
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        self.subscribed_streams: Set[str] = set()
        self.price_cache = get_price_cache()
        self._task: Optional[asyncio.Task] = None

    async def start(self, streams: list[str]):
        if self.running:
            logger.warning("WebSocket manager already running")
            return

        logger.info(f"Starting WebSocket manager with {len(streams)} streams")
        self.subscribed_streams = set(streams)
        self.running = True
        self._task = asyncio.create_task(self._maintain_connection())
        logger.info("WebSocket manager started successfully")

    async def stop(self):
        logger.info("Stopping WebSocket manager")
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket manager stopped")

    async def _maintain_connection(self):
        current_delay = self.reconnect_delay

        while self.running:
            try:
                await self._connect_and_listen()
                current_delay = self.reconnect_delay
            except asyncio.CancelledError:
                logger.info("WebSocket connection task cancelled")
                break
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                if self.running:
                    logger.info(f"Reconnecting in {current_delay} seconds")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 2, self.max_reconnect_delay)

    async def _connect_and_listen(self):
        if not self.subscribed_streams:
            logger.warning("No streams subscribed")
            await asyncio.sleep(1)
            return

        streams_param = "/".join(self.subscribed_streams)
        url = f"{self.base_url}/stream?streams={streams_param}"
        logger.info(f"Connecting to Binance WebSocket: {len(self.subscribed_streams)} streams")

        try:
            async with connect(url, ping_interval=20, ping_timeout=10) as websocket:
                self.ws = websocket
                logger.info("WebSocket connected successfully")

                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        await self._handle_message(data)
                    except asyncio.TimeoutError:
                        continue
                    except ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode WebSocket message: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            raise

    async def _handle_message(self, data: dict):
        if "stream" not in data or "data" not in data:
            return

        stream = data["stream"]
        msg_data = data["data"]

        if "@miniTicker" in stream or "@ticker" in stream:
            await self._handle_ticker_message(msg_data)
        elif "@depth" in stream:
            await self._handle_depth_message(msg_data)

    async def _handle_ticker_message(self, data: dict):
        try:
            symbol = data.get("s")
            if not symbol:
                return

            if "c" in data:
                price = Decimal(data["c"])
                timestamp = datetime.fromtimestamp(data.get("E", 0) / 1000)
                self.price_cache.update_price(symbol, price, timestamp)

            if "p" in data and "P" in data:
                ticker_data = {
                    "symbol": symbol,
                    "price_change": Decimal(data.get("p", "0")),
                    "price_change_percent": Decimal(data.get("P", "0")),
                    "weighted_avg_price": Decimal(data.get("w", "0")),
                    "prev_close_price": Decimal(data.get("x", "0")),
                    "last_price": Decimal(data.get("c", "0")),
                    "last_qty": Decimal(data.get("Q", "0")),
                    "bid_price": Decimal(data.get("b", "0")),
                    "bid_qty": Decimal(data.get("B", "0")),
                    "ask_price": Decimal(data.get("a", "0")),
                    "ask_qty": Decimal(data.get("A", "0")),
                    "open_price": Decimal(data.get("o", "0")),
                    "high_price": Decimal(data.get("h", "0")),
                    "low_price": Decimal(data.get("l", "0")),
                    "volume": Decimal(data.get("v", "0")),
                    "quote_volume": Decimal(data.get("q", "0")),
                    "open_time": datetime.fromtimestamp(data.get("O", 0) / 1000),
                    "close_time": datetime.fromtimestamp(data.get("C", 0) / 1000),
                    "first_id": data.get("F", 0),
                    "last_id": data.get("L", 0),
                    "count": data.get("n", 0),
                    "timestamp": datetime.utcnow()
                }
                self.price_cache.update_ticker(symbol, ticker_data)
        except Exception:
            pass

    async def _handle_depth_message(self, data: dict):
        pass

    def add_stream(self, stream: str):
        self.subscribed_streams.add(stream)

    def remove_stream(self, stream: str):
        self.subscribed_streams.discard(stream)

    @property
    def is_connected(self) -> bool:
        if self.ws is None:
            return False
        # Check if websocket is open (compatible with websockets library)
        try:
            return hasattr(self.ws, 'closed') and not self.ws.closed
        except AttributeError:
            # For newer versions of websockets library
            return self.ws.open if hasattr(self.ws, 'open') else self.running


_ws_manager_instance: Optional[BinanceWebSocketManager] = None


def get_ws_manager() -> BinanceWebSocketManager:
    global _ws_manager_instance
    if _ws_manager_instance is None:
        _ws_manager_instance = BinanceWebSocketManager()
    return _ws_manager_instance
