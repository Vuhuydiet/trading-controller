from sqlmodel import Session
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from app.modules.market.infrastructure.market_data_repository import MarketDataRepository
from app.modules.market.infrastructure.price_cache import get_price_cache
from app.modules.market.domain.ticker import Ticker
from .dtos import TickerResponse, TickersResponse


class GetTickerHandler:
    def __init__(self, session: Session):
        self.session = session
        self.binance_client = BinanceRestClient()
        self.repository = MarketDataRepository(session)
        self.price_cache = get_price_cache()

    async def handle(self, symbol: str) -> TickerResponse:
        symbol_upper = symbol.upper()

        cached_ticker = self.price_cache.get_ticker(symbol_upper)
        if cached_ticker:
            return TickerResponse(**cached_ticker)

        cached_ticker_db = self.repository.get_cached_ticker(symbol_upper, max_age_seconds=10)
        if cached_ticker_db:
            response = TickerResponse.model_validate(cached_ticker_db)
            response.timestamp = datetime.utcnow()
            return response

        raw_ticker = await self.binance_client.get_ticker_24hr(symbol_upper)

        if isinstance(raw_ticker, list):
            raise ValueError(f"Expected single ticker for symbol {symbol_upper}, got list")

        ticker = Ticker(
            symbol=raw_ticker["symbol"],
            price_change=Decimal(raw_ticker["priceChange"]),
            price_change_percent=Decimal(raw_ticker["priceChangePercent"]),
            weighted_avg_price=Decimal(raw_ticker["weightedAvgPrice"]),
            prev_close_price=Decimal(raw_ticker["prevClosePrice"]),
            last_price=Decimal(raw_ticker["lastPrice"]),
            last_qty=Decimal(raw_ticker["lastQty"]),
            bid_price=Decimal(raw_ticker["bidPrice"]),
            bid_qty=Decimal(raw_ticker["bidQty"]),
            ask_price=Decimal(raw_ticker["askPrice"]),
            ask_qty=Decimal(raw_ticker["askQty"]),
            open_price=Decimal(raw_ticker["openPrice"]),
            high_price=Decimal(raw_ticker["highPrice"]),
            low_price=Decimal(raw_ticker["lowPrice"]),
            volume=Decimal(raw_ticker["volume"]),
            quote_volume=Decimal(raw_ticker["quoteVolume"]),
            open_time=datetime.fromtimestamp(raw_ticker["openTime"] / 1000),
            close_time=datetime.fromtimestamp(raw_ticker["closeTime"] / 1000),
            first_id=raw_ticker["firstId"],
            last_id=raw_ticker["lastId"],
            count=raw_ticker["count"]
        )

        self.repository.save_ticker(ticker)

        response = TickerResponse.model_validate(ticker)
        response.timestamp = datetime.utcnow()

        ticker_dict = response.model_dump()
        self.price_cache.update_ticker(symbol_upper, ticker_dict)

        return response


class GetTickersHandler:
    def __init__(self, session: Session):
        self.session = session
        self.binance_client = BinanceRestClient()
        self.price_cache = get_price_cache()

    async def handle(self, symbols: Optional[List[str]] = None) -> TickersResponse:
        timestamp = datetime.utcnow()

        if symbols:
            symbols_upper = [s.upper() for s in symbols]
            tickers = []

            for symbol in symbols_upper:
                cached_ticker = self.price_cache.get_ticker(symbol)
                if cached_ticker:
                    tickers.append(TickerResponse(**cached_ticker))
                else:
                    try:
                        raw_ticker = await self.binance_client.get_ticker_24hr(symbol)
                        if not isinstance(raw_ticker, list):
                            ticker_response = self._create_ticker_response(raw_ticker, timestamp)
                            ticker_dict = ticker_response.model_dump()
                            self.price_cache.update_ticker(symbol, ticker_dict)
                            tickers.append(ticker_response)
                    except Exception:
                        continue

            return TickersResponse(tickers=tickers, timestamp=timestamp)

        cached_tickers = self.price_cache.get_all_tickers()
        if cached_tickers:
            tickers = [TickerResponse(**data) for data in cached_tickers.values()]
            return TickersResponse(tickers=tickers, timestamp=timestamp)

        try:
            all_tickers = await self.binance_client.get_ticker_24hr()

            if not isinstance(all_tickers, list):
                all_tickers = [all_tickers]

            tickers = []
            for raw_ticker in all_tickers:
                ticker_response = self._create_ticker_response(raw_ticker, timestamp)
                ticker_dict = ticker_response.model_dump()
                self.price_cache.update_ticker(raw_ticker["symbol"], ticker_dict)
                tickers.append(ticker_response)

            return TickersResponse(tickers=tickers, timestamp=timestamp)
        except Exception as e:
            raise ValueError(f"Failed to fetch tickers: {str(e)}")

    def _create_ticker_response(self, raw_ticker: dict, timestamp: datetime) -> TickerResponse:
        return TickerResponse(
            symbol=raw_ticker["symbol"],
            price_change=Decimal(raw_ticker["priceChange"]),
            price_change_percent=Decimal(raw_ticker["priceChangePercent"]),
            weighted_avg_price=Decimal(raw_ticker["weightedAvgPrice"]),
            prev_close_price=Decimal(raw_ticker["prevClosePrice"]),
            last_price=Decimal(raw_ticker["lastPrice"]),
            last_qty=Decimal(raw_ticker["lastQty"]),
            bid_price=Decimal(raw_ticker["bidPrice"]),
            bid_qty=Decimal(raw_ticker["bidQty"]),
            ask_price=Decimal(raw_ticker["askPrice"]),
            ask_qty=Decimal(raw_ticker["askQty"]),
            open_price=Decimal(raw_ticker["openPrice"]),
            high_price=Decimal(raw_ticker["highPrice"]),
            low_price=Decimal(raw_ticker["lowPrice"]),
            volume=Decimal(raw_ticker["volume"]),
            quote_volume=Decimal(raw_ticker["quoteVolume"]),
            open_time=datetime.fromtimestamp(raw_ticker["openTime"] / 1000),
            close_time=datetime.fromtimestamp(raw_ticker["closeTime"] / 1000),
            first_id=raw_ticker["firstId"],
            last_id=raw_ticker["lastId"],
            count=raw_ticker["count"],
            timestamp=timestamp
        )
