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
        aligner: NewsPriceAligner 
    ):
        self.sentiment_bot = sentiment_bot
        self.reasoning_bot = reasoning_bot
        self.repo = repo
        self.aligner = aligner

    async def execute(self, request: AnalyzeNewsRequest) -> AnalyzeNewsResponse:
        # 1. Chạy News-Price Aligner
        aligned_context = await self.aligner.align_data_for_ai(
            news_content=request.news_content,
            published_at=request.published_at
        )

        # 2. Tạo task chạy song song (Chưa chạy ngay, chỉ mới lên nòng)
        sentiment_task = self.sentiment_bot.analyze_sentiment(request.news_content)
        reasoning_task = self.reasoning_bot.explain_market_trend(news=aligned_context)


        sentiment_res, reasoning_result = await asyncio.gather(sentiment_task, reasoning_task)

        await self.repo.save_analysis_result(
            news_id=request.news_id,
            sentiment=sentiment_res['label'],
            confidence=sentiment_res['score'],
            trend=reasoning_result['trend'],
            reasoning=reasoning_result['reasoning']
        )

        return AnalyzeNewsResponse(
            sentiment=sentiment_res['label'],
            confidence=sentiment_res['score'],
            trend=reasoning_result['trend'],
            reasoning=reasoning_result['reasoning']
        )