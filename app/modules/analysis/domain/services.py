from datetime import datetime
from app.modules.market.public_api import get_price_movements

class NewsPriceAligner:
    """
    Service này chịu trách nhiệm chuẩn bị dữ liệu đầu vào sạch sẽ cho AI.
    Nó 'khớp' (align) nội dung tin tức với biến động giá tương ứng.
    """
    async def align_data_for_ai(self, news_content: str, published_at: datetime) -> str:
        # 1. Gọi sang Market module để lấy dữ liệu giá
        market_context = await get_price_movements(symbol="BTCUSDT", target_time=published_at)
        
        # 2. Tạo ra một context hoàn chỉnh (Prompt Context)
        aligned_context = f"""
        --- NEWS CONTENT ---
        "{news_content}"
        Published at: {published_at}
        
        --- MARKET REACTION ---
        {market_context}
        """
        return aligned_context