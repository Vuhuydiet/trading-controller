import asyncio
from .dtos import AnalyzeNewsRequest, AnalyzeNewsResponse
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort, AnalysisRepositoryPort
from app.modules.analysis.domain.services import NewsPriceAligner

class AnalyzeNewsHandler:
    def __init__(
        self, 
        sentiment_bot: SentimentAnalyzerPort, 
        reasoning_bot: MarketReasonerPort,   
        repo: AnalysisRepositoryPort,
        aligner: NewsPriceAligner # <--- Component mới thêm vào
    ):
        self.sentiment_bot = sentiment_bot
        self.reasoning_bot = reasoning_bot
        self.repo = repo
        self.aligner = aligner

    async def execute(self, request: AnalyzeNewsRequest) -> AnalyzeNewsResponse:
        # 1. Chạy News-Price Aligner (Logic tách biệt, không nằm trong handler nữa)
        # Kết quả: context chứa cả tin lẫn giá
        aligned_context = await self.aligner.align_data_for_ai(
            news_content=request.news_content,
            published_at=request.published_at
        )

        # 2. Chạy AI song song (Sentiment & Reasoner)
        # - Sentiment chỉ cần đọc tin
        # - Reasoner cần đọc cả tin lẫn giá (aligned_context) để giải thích nhân quả
        sentiment_task = self.sentiment_bot.analyze_sentiment(request.news_content)
        reasoning_task = self.reasoning_bot.explain_market_trend(
            news=aligned_context, 
            price_change=0 # Aligner đã lo phần text mô tả giá rồi, tham số này có thể bỏ hoặc để 0
        )

        sentiment_res, reasoning_res = await asyncio.gather(sentiment_task, reasoning_task)

        # 3. Lưu vào DB
        await self.repo.save_analysis_result(
            news_id=request.news_id,
            sentiment=sentiment_res['label'],
            confidence=sentiment_res['score'],
            reasoning=reasoning_res
        )

        return AnalyzeNewsResponse(
            sentiment=sentiment_res['label'],
            confidence=sentiment_res['score'],
            reasoning=reasoning_res
        )