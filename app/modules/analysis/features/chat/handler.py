
from app.modules.analysis.features.chat.dtos import ChatResponse, UserIntent
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo
from app.modules.subscription.domain import plan


class ChatHandler:
    def __init__(self, reasoner, price_service, repo: SqlModelAnalysisRepo):
        self.reasoner = reasoner
        self.price_service = price_service
        self.repo = repo

    async def handle_chat(self, message: str) -> ChatResponse: # Thêm type hint return
        # BƯỚC 1: AI xác định cần làm gì (Return Dict)
        plan_dict = await self.reasoner.extract_intent(message)
        
        try:
            intent = UserIntent(**plan_dict) 
        except Exception:
            # Fallback nếu AI trả về json lung tung
            intent = UserIntent(intent_type="general_chat", symbols=[])

        context_data = ""
        data_sources = [] # Lưu lại nguồn để trả về frontend

        # BƯỚC 2: Backend đi gom dữ liệu (Executor)
        # Bây giờ bạn có thể dùng dấu chấm (.) thay vì ngoặc vuông ['']
        if intent.symbols: 
            for symbol in intent.symbols:
                # 1. Lấy giá
                price_info = await self.price_service.get_ticker_24hr(symbol)
                
                # 2. Lấy tin tức (nếu cần)
                news_info = []
                if intent.intent_type == "market_insight":
                    search_term = symbol.replace("USDT", "").replace("USDC", "")
                    
                    # Gọi repo với search_term ngắn gọn (BTC)
                    news_info = await self.repo.get_recent_news(search_term)
                
                # 3. Tổng hợp lại thành text
                context_data += f"\n--- Data for {symbol} ---\n"
                context_data += f"Price: {price_info}\n"
                
                data_sources.append(f"Binance Ticker: {symbol}")
                
                if news_info:
                    news_text_list = []
                    for news in news_info:
                        news_text_list.append(f"- {news.title} (Source: {news.source})")
                        
                        data_sources.append(f"News ({news.source}): {news.title}") 

                    context_data += "Related News:\n" + "\n".join(news_text_list) + "\n"
                else:
                    context_data += "No recent news found.\n"

        # BƯỚC 3: AI viết câu trả lời cuối cùng
        final_prompt = f"""
        User Question: "{message}"
        
        Real-time Market Data:
        {context_data}
        
        Task: Answer the user naturally based ONLY on the data above.
        """
        
        ai_reply_text = await self.reasoner.chat(final_prompt)

        # --- QUAN TRỌNG: Trả về đúng object ChatResponse ---
        # Router đang đợi response_model=ChatResponse, không được trả về string trần
        return ChatResponse(
            reply=ai_reply_text,
            data_sources=data_sources
        )
      