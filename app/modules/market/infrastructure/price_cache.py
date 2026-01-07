from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal


class PriceCache:
    def __init__(self):
        self._prices: Dict[str, Dict] = {}
        self._tickers: Dict[str, Dict] = {}

    def update_price(self, symbol: str, price: Decimal, timestamp: datetime):
        self._prices[symbol] = {
            "symbol": symbol,
            "price": price,
            "timestamp": timestamp
        }

    def get_price(self, symbol: str) -> Optional[Dict]:
        return self._prices.get(symbol)

    def get_all_prices(self) -> Dict[str, Dict]:
        return self._prices.copy()

    def update_ticker(self, symbol: str, ticker_data: Dict):
        ticker_data["timestamp"] = datetime.utcnow()
        self._tickers[symbol] = ticker_data

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        return self._tickers.get(symbol)

    def get_all_tickers(self) -> Dict[str, Dict]:
        return self._tickers.copy()

    def clear(self):
        self._prices.clear()
        self._tickers.clear()


_price_cache_instance = PriceCache()


def get_price_cache() -> PriceCache:
    return _price_cache_instance
