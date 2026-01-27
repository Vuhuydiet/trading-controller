# app/modules/market/public_api.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from app.shared.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton client instance
_binance_client: Optional[BinanceRestClient] = None


def get_binance_client() -> BinanceRestClient:
    global _binance_client
    if _binance_client is None:
        _binance_client = BinanceRestClient()
    return _binance_client


async def get_price_movements(
    symbol: str,
    target_time: datetime,
    window_hours: int = 1
) -> str:
    """
    Trả về mô tả biến động giá xung quanh thời điểm target_time.
    Lấy giá trước và sau tin ra trong khoảng window_hours.

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        target_time: Thời điểm tin tức xuất hiện
        window_hours: Số giờ trước/sau để phân tích (default: 1h)

    Returns:
        Mô tả biến động giá dưới dạng text
    """
    client = get_binance_client()

    try:
        # Ensure target_time has timezone
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        # Calculate time windows
        before_time = target_time - timedelta(hours=window_hours)
        after_time = target_time + timedelta(hours=window_hours)

        # Convert to milliseconds for Binance API
        start_ms = int(before_time.timestamp() * 1000)
        end_ms = int(after_time.timestamp() * 1000)

        # Get klines data (1-minute candles for precision)
        klines = await client.get_klines(
            symbol=symbol,
            interval="1m",
            start_time=start_ms,
            end_time=end_ms,
            limit=500  # ~8 hours of 1-min data
        )

        if not klines or len(klines) < 2:
            logger.warning(f"Insufficient kline data for {symbol} at {target_time}")
            return f"Insufficient price data for {symbol} around {target_time.isoformat()}"

        # Parse kline data
        # Kline format: [open_time, open, high, low, close, volume, ...]
        price_before = float(klines[0][1])  # Open price of first candle
        price_at_news = _find_price_at_time(klines, target_time)
        price_after = float(klines[-1][4])  # Close price of last candle

        # Calculate price changes
        change_before_to_news = ((price_at_news - price_before) / price_before) * 100
        change_news_to_after = ((price_after - price_at_news) / price_at_news) * 100
        total_change = ((price_after - price_before) / price_before) * 100

        # Calculate high/low in the period
        high_price = max(float(k[2]) for k in klines)
        low_price = min(float(k[3]) for k in klines)
        volatility = ((high_price - low_price) / price_before) * 100

        # Calculate volume
        total_volume = sum(float(k[5]) for k in klines)

        # Build description
        direction = "increased" if total_change > 0 else "decreased" if total_change < 0 else "remained stable"
        reaction = "positive" if change_news_to_after > 0 else "negative" if change_news_to_after < 0 else "neutral"

        description = f"""Price Analysis for {symbol}:
- Price before news ({before_time.strftime('%H:%M UTC')}): ${price_before:,.2f}
- Price at news time ({target_time.strftime('%H:%M UTC')}): ${price_at_news:,.2f}
- Price after news ({after_time.strftime('%H:%M UTC')}): ${price_after:,.2f}
- Total change: {total_change:+.2f}%
- Immediate reaction (after news): {change_news_to_after:+.2f}%
- Period high: ${high_price:,.2f}, low: ${low_price:,.2f}
- Volatility: {volatility:.2f}%
- Total volume: {total_volume:,.2f}
- Market reaction: {reaction.upper()} - Price {direction} by {abs(total_change):.2f}% within {window_hours}h after the news."""

        return description

    except Exception as e:
        logger.error(f"Error getting price movements for {symbol}: {e}")
        return f"Error retrieving price data for {symbol}: {str(e)}"


def _find_price_at_time(klines: list, target_time: datetime) -> float:
    """Find the price closest to the target time"""
    target_ms = int(target_time.timestamp() * 1000)

    closest_kline = None
    min_diff = float('inf')

    for kline in klines:
        kline_time = kline[0]  # Open time in ms
        diff = abs(kline_time - target_ms)
        if diff < min_diff:
            min_diff = diff
            closest_kline = kline

    if closest_kline:
        return float(closest_kline[4])  # Close price

    return float(klines[len(klines)//2][4])  # Middle candle as fallback


async def get_price_at_time(symbol: str, target_time: datetime) -> Optional[float]:
    """Get price at a specific time"""
    client = get_binance_client()

    try:
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        target_ms = int(target_time.timestamp() * 1000)

        klines = await client.get_klines(
            symbol=symbol,
            interval="1m",
            start_time=target_ms - 60000,  # 1 minute before
            end_time=target_ms + 60000,    # 1 minute after
            limit=5
        )

        if klines:
            return float(klines[0][4])  # Close price
        return None

    except Exception as e:
        logger.error(f"Error getting price at time for {symbol}: {e}")
        return None


async def get_price_change_metrics(
    symbol: str,
    period_from: datetime,
    period_to: datetime
) -> Dict[str, Any]:
    """
    Get detailed price change metrics between two time periods.
    Used for causal analysis.
    """
    client = get_binance_client()

    try:
        if period_from.tzinfo is None:
            period_from = period_from.replace(tzinfo=timezone.utc)
        if period_to.tzinfo is None:
            period_to = period_to.replace(tzinfo=timezone.utc)

        start_ms = int(period_from.timestamp() * 1000)
        end_ms = int(period_to.timestamp() * 1000)

        # Determine appropriate interval based on period length
        period_hours = (period_to - period_from).total_seconds() / 3600
        if period_hours <= 2:
            interval = "1m"
        elif period_hours <= 24:
            interval = "5m"
        elif period_hours <= 168:  # 1 week
            interval = "1h"
        else:
            interval = "4h"

        klines = await client.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_ms,
            end_time=end_ms,
            limit=500
        )

        if not klines or len(klines) < 2:
            return {
                "error": "Insufficient data",
                "price_from": 0,
                "price_to": 0,
                "change_percent": 0,
                "volatility": 0,
                "volume": 0
            }

        price_from = float(klines[0][1])
        price_to = float(klines[-1][4])
        high = max(float(k[2]) for k in klines)
        low = min(float(k[3]) for k in klines)
        volume = sum(float(k[5]) for k in klines)

        change_percent = ((price_to - price_from) / price_from) * 100 if price_from > 0 else 0
        volatility = ((high - low) / price_from) * 100 if price_from > 0 else 0

        # Calculate trend strength
        up_candles = sum(1 for k in klines if float(k[4]) > float(k[1]))
        down_candles = len(klines) - up_candles
        trend_strength = (up_candles - down_candles) / len(klines)

        return {
            "price_from": price_from,
            "price_to": price_to,
            "change_percent": round(change_percent, 4),
            "high": high,
            "low": low,
            "volatility": round(volatility, 4),
            "volume": volume,
            "trend_strength": round(trend_strength, 4),  # -1 to 1
            "up_candles": up_candles,
            "down_candles": down_candles,
            "total_candles": len(klines)
        }

    except Exception as e:
        logger.error(f"Error getting price metrics for {symbol}: {e}")
        return {
            "error": str(e),
            "price_from": 0,
            "price_to": 0,
            "change_percent": 0,
            "volatility": 0,
            "volume": 0
        }
