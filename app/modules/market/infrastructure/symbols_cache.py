from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient


class SymbolsCache:
    def __init__(self):
        self._cache: Dict[str, any] = {}
        self._symbols_list: List[Dict] = []
        self._last_update: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)
        self.binance_client = BinanceRestClient()

    def _is_cache_valid(self) -> bool:
        if not self._last_update:
            return False
        return datetime.utcnow() - self._last_update < self._cache_duration

    async def get_all_symbols(self) -> List[Dict]:
        if self._is_cache_valid() and self._symbols_list:
            return self._symbols_list

        exchange_info = await self.binance_client.get_exchange_info()
        self._symbols_list = exchange_info.get("symbols", [])
        self._last_update = datetime.utcnow()

        for symbol_data in self._symbols_list:
            symbol = symbol_data.get("symbol")
            if symbol:
                self._cache[symbol] = symbol_data

        return self._symbols_list

    async def get_symbol(self, symbol: str) -> Optional[Dict]:
        if self._is_cache_valid() and symbol in self._cache:
            return self._cache[symbol]

        await self.get_all_symbols()
        return self._cache.get(symbol)

    async def refresh_cache(self) -> None:
        self._last_update = None
        await self.get_all_symbols()

    def clear_cache(self) -> None:
        self._cache.clear()
        self._symbols_list.clear()
        self._last_update = None


_symbols_cache_instance = SymbolsCache()


def get_symbols_cache() -> SymbolsCache:
    return _symbols_cache_instance
