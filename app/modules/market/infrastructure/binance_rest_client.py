import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.shared.core.config import settings
from app.shared.core.logging_config import get_logger

logger = get_logger(__name__)


class BinanceAPIError(Exception):
    pass


class BinanceRateLimitError(Exception):
    pass


class BinanceRestClient:
    def __init__(self):
        self.base_url = settings.BINANCE_API_BASE_URL
        self.api_key = settings.BINANCE_API_KEY
        self.api_secret = settings.BINANCE_API_SECRET
        self._rate_limit_lock = asyncio.Lock()
        self._request_timestamps: List[datetime] = []
        self._max_requests_per_minute = 1200
        self._retry_attempts = 3
        self._retry_delay = 1.0

    async def _check_rate_limit(self):
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            one_minute_ago = now - timedelta(minutes=1)

            self._request_timestamps = [
                ts for ts in self._request_timestamps if ts > one_minute_ago
            ]

            if len(self._request_timestamps) >= self._max_requests_per_minute:
                logger.warning("Rate limit approaching, waiting before request")
                await asyncio.sleep(1.0)
                self._request_timestamps = [
                    ts for ts in self._request_timestamps
                    if ts > datetime.utcnow() - timedelta(minutes=1)
                ]

            self._request_timestamps.append(now)

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._check_rate_limit()

        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self._retry_attempts):
            try:
                logger.info(f"Binance API call: {method} {endpoint} (attempt {attempt + 1})")

                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        timeout=10.0
                    )

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit hit, retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code >= 500:
                        logger.error(f"Binance server error: {response.status_code}")
                        if attempt < self._retry_attempts - 1:
                            await asyncio.sleep(self._retry_delay * (attempt + 1))
                            continue
                        raise BinanceAPIError(f"Binance server error: {response.status_code}")

                    response.raise_for_status()
                    logger.info(f"Binance API success: {method} {endpoint}")
                    return response.json()

            except httpx.TimeoutException:
                logger.error(f"Binance API timeout: {endpoint}")
                if attempt < self._retry_attempts - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise BinanceAPIError("Binance API timeout")

            except httpx.NetworkError as e:
                logger.error(f"Binance network error: {str(e)}")
                if attempt < self._retry_attempts - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise BinanceAPIError(f"Network error: {str(e)}")

            except Exception as e:
                logger.error(f"Unexpected error calling Binance API: {str(e)}")
                raise BinanceAPIError(f"API call failed: {str(e)}")

        raise BinanceAPIError("Max retry attempts exceeded")

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List[Any]]:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._request("GET", "/api/v3/klines", params)

    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> Dict[str, Any] | List[Dict[str, Any]]:
        params = {}
        if symbol:
            params["symbol"] = symbol

        return await self._request("GET", "/api/v3/ticker/24hr", params)

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        params = {
            "symbol": symbol,
            "limit": limit
        }

        return await self._request("GET", "/api/v3/depth", params)

    async def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if symbol:
            params["symbol"] = symbol

        return await self._request("GET", "/api/v3/exchangeInfo", params)

    async def ping(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v3/ping")
