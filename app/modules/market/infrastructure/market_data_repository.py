from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime, timedelta
from app.modules.market.domain.kline import Kline
from app.modules.market.domain.ticker import Ticker
from app.modules.market.domain.order_book import OrderBook


class MarketDataRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_cached_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Kline]:
        statement = (
            select(Kline)
            .where(Kline.symbol == symbol)
            .where(Kline.interval == interval)
            .where(Kline.open_time >= start_time)
            .where(Kline.open_time <= end_time)
            .order_by(Kline.open_time)
        )
        return list(self.session.exec(statement).all())

    def save_klines(self, klines: List[Kline]) -> None:
        for kline in klines:
            existing = self.session.exec(
                select(Kline)
                .where(Kline.symbol == kline.symbol)
                .where(Kline.interval == kline.interval)
                .where(Kline.open_time == kline.open_time)
            ).first()

            if existing:
                existing.close_time = kline.close_time
                existing.open_price = kline.open_price
                existing.high_price = kline.high_price
                existing.low_price = kline.low_price
                existing.close_price = kline.close_price
                existing.volume = kline.volume
                existing.quote_asset_volume = kline.quote_asset_volume
                existing.number_of_trades = kline.number_of_trades
                existing.taker_buy_base_volume = kline.taker_buy_base_volume
                existing.taker_buy_quote_volume = kline.taker_buy_quote_volume
                existing.created_at = datetime.utcnow()
            else:
                self.session.add(kline)

        self.session.commit()

    def get_cached_ticker(self, symbol: str, max_age_seconds: int = 10) -> Optional[Ticker]:
        cutoff_time = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        statement = (
            select(Ticker)
            .where(Ticker.symbol == symbol)
            .where(Ticker.updated_at >= cutoff_time)
        )
        return self.session.exec(statement).first()

    def save_ticker(self, ticker: Ticker) -> None:
        existing = self.session.exec(
            select(Ticker).where(Ticker.symbol == ticker.symbol)
        ).first()

        if existing:
            existing.price_change = ticker.price_change
            existing.price_change_percent = ticker.price_change_percent
            existing.weighted_avg_price = ticker.weighted_avg_price
            existing.prev_close_price = ticker.prev_close_price
            existing.last_price = ticker.last_price
            existing.last_qty = ticker.last_qty
            existing.bid_price = ticker.bid_price
            existing.bid_qty = ticker.bid_qty
            existing.ask_price = ticker.ask_price
            existing.ask_qty = ticker.ask_qty
            existing.open_price = ticker.open_price
            existing.high_price = ticker.high_price
            existing.low_price = ticker.low_price
            existing.volume = ticker.volume
            existing.quote_volume = ticker.quote_volume
            existing.open_time = ticker.open_time
            existing.close_time = ticker.close_time
            existing.first_id = ticker.first_id
            existing.last_id = ticker.last_id
            existing.count = ticker.count
            existing.updated_at = datetime.utcnow()
        else:
            self.session.add(ticker)

        self.session.commit()

    def get_cached_order_book(self, symbol: str, max_age_seconds: int = 5) -> Optional[OrderBook]:
        cutoff_time = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        statement = (
            select(OrderBook)
            .where(OrderBook.symbol == symbol)
            .where(OrderBook.updated_at >= cutoff_time)
        )
        return self.session.exec(statement).first()

    def save_order_book(self, order_book: OrderBook) -> None:
        existing = self.session.exec(
            select(OrderBook).where(OrderBook.symbol == order_book.symbol)
        ).first()

        if existing:
            existing.last_update_id = order_book.last_update_id
            existing.bids = order_book.bids
            existing.asks = order_book.asks
            existing.updated_at = datetime.utcnow()
        else:
            self.session.add(order_book)

        self.session.commit()

    def cleanup_old_klines(self, days: int = 30) -> None:
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        statement = select(Kline).where(Kline.created_at < cutoff_time)
        old_klines = self.session.exec(statement).all()

        for kline in old_klines:
            self.session.delete(kline)

        self.session.commit()
