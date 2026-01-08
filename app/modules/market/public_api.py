# app/modules/market/public_api.py
from datetime import datetime

async def get_price_movements(symbol: str, target_time: datetime) -> str:
    """
    Trả về mô tả biến động giá xung quanh thời điểm target_time.
    Ví dụ: Lấy giá trước và sau tin ra 1 tiếng.
    """
    # Logic giả định:
    # 1. start = target_time - 1h
    # 2. end = target_time + 1h
    # 3. prices = market_repo.get_candles(symbol, start, end)
    
    # TODO: Thay bằng logic thật
    return f"Price of {symbol} dropped 2.5% from 65000 to 63375 within 1 hour after the news."