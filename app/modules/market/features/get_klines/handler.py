from sqlmodel import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from app.modules.market.infrastructure.market_data_repository import MarketDataRepository
from app.modules.market.domain.kline import Kline
from .dtos import KlineRequest, KlineResponse


class GetKlinesHandler:
    def __init__(self, session: Session):
        self.session = session
        self.binance_client = BinanceRestClient()
        self.repository = MarketDataRepository(session)

    @staticmethod
    def parse_timestamp(timestamp_str: Optional[str]) -> Optional[int]:
        if not timestamp_str:
            return None

        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except (ValueError, AttributeError):
            return int(timestamp_str)

    async def handle(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 500
    ) -> List[KlineResponse]:
        symbol_upper = symbol.upper()

        request = KlineRequest(
            symbol=symbol_upper,
            interval=interval,
            start_time=self.parse_timestamp(start_time),
            end_time=self.parse_timestamp(end_time),
            limit=limit
        )

        if request.start_time and request.end_time:
            start_dt = datetime.fromtimestamp(request.start_time / 1000)
            end_dt = datetime.fromtimestamp(request.end_time / 1000)

            cached_klines = self.repository.get_cached_klines(
                request.symbol,
                request.interval,
                start_dt,
                end_dt
            )

            if cached_klines and len(cached_klines) >= request.limit:
                return [self._create_kline_response(k) for k in cached_klines[:request.limit]]

        raw_klines = await self.binance_client.get_klines(
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )

        klines = []
        for raw in raw_klines:
            kline = Kline(
                symbol=request.symbol,
                interval=request.interval,
                open_time=datetime.fromtimestamp(raw[0] / 1000),
                close_time=datetime.fromtimestamp(raw[6] / 1000),
                open_price=Decimal(raw[1]),
                high_price=Decimal(raw[2]),
                low_price=Decimal(raw[3]),
                close_price=Decimal(raw[4]),
                volume=Decimal(raw[5]),
                quote_asset_volume=Decimal(raw[7]),
                number_of_trades=int(raw[8]),
                taker_buy_base_volume=Decimal(raw[9]),
                taker_buy_quote_volume=Decimal(raw[10])
            )
            klines.append(kline)

        if klines:
            self.repository.save_klines(klines)

        return [self._create_kline_response(k) for k in klines]

    def _create_kline_response(self, kline: Kline) -> KlineResponse:
        return KlineResponse(
            symbol=kline.symbol,
            interval=kline.interval,
            open_time=kline.open_time,
            open=kline.open_price,
            high=kline.high_price,
            low=kline.low_price,
            close=kline.close_price,
            volume=kline.volume,
            close_time=kline.close_time
        )
