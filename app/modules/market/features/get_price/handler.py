from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from app.modules.market.infrastructure.price_cache import get_price_cache
from .dtos import PriceResponse, PricesResponse


class GetPriceHandler:
    def __init__(self):
        self.binance_client = BinanceRestClient()
        self.price_cache = get_price_cache()

    async def handle(self, symbol: str) -> PriceResponse:
        symbol_upper = symbol.upper()

        cached_price = self.price_cache.get_price(symbol_upper)
        if cached_price:
            return PriceResponse(
                symbol=cached_price["symbol"],
                price=cached_price["price"],
                timestamp=cached_price["timestamp"]
            )

        try:
            ticker_data = await self.binance_client.get_ticker_24hr(symbol_upper)

            if isinstance(ticker_data, list):
                raise ValueError(f"Expected single ticker for symbol {symbol_upper}, got list")

            price = Decimal(ticker_data["lastPrice"])
            timestamp = datetime.utcnow()

            self.price_cache.update_price(symbol_upper, price, timestamp)

            return PriceResponse(
                symbol=symbol_upper,
                price=price,
                timestamp=timestamp
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch price for {symbol_upper}: {str(e)}")


class GetPricesHandler:
    def __init__(self):
        self.binance_client = BinanceRestClient()
        self.price_cache = get_price_cache()

    async def handle(self, symbols: Optional[List[str]] = None) -> PricesResponse:
        timestamp = datetime.utcnow()

        if symbols:
            symbols_upper = [s.upper() for s in symbols]
            prices = []

            for symbol in symbols_upper:
                cached_price = self.price_cache.get_price(symbol)
                if cached_price:
                    prices.append(PriceResponse(
                        symbol=cached_price["symbol"],
                        price=cached_price["price"],
                        timestamp=cached_price["timestamp"]
                    ))
                else:
                    try:
                        ticker_data = await self.binance_client.get_ticker_24hr(symbol)
                        if not isinstance(ticker_data, list):
                            price = Decimal(ticker_data["lastPrice"])
                            self.price_cache.update_price(symbol, price, timestamp)
                            prices.append(PriceResponse(
                                symbol=symbol,
                                price=price,
                                timestamp=timestamp
                            ))
                    except Exception:
                        continue

            return PricesResponse(prices=prices, timestamp=timestamp)

        cached_prices = self.price_cache.get_all_prices()
        if cached_prices:
            prices = [
                PriceResponse(
                    symbol=data["symbol"],
                    price=data["price"],
                    timestamp=data["timestamp"]
                )
                for data in cached_prices.values()
            ]
            return PricesResponse(prices=prices, timestamp=timestamp)

        try:
            all_tickers = await self.binance_client.get_ticker_24hr()

            if not isinstance(all_tickers, list):
                all_tickers = [all_tickers]

            prices = []
            for ticker_data in all_tickers:
                symbol = ticker_data["symbol"]
                price = Decimal(ticker_data["lastPrice"])
                self.price_cache.update_price(symbol, price, timestamp)
                prices.append(PriceResponse(
                    symbol=symbol,
                    price=price,
                    timestamp=timestamp
                ))

            return PricesResponse(prices=prices, timestamp=timestamp)
        except Exception as e:
            raise ValueError(f"Failed to fetch prices: {str(e)}")
