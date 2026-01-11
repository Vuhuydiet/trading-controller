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

        # 2. Run sentiment and reasoning analysis in parallel
        sentiment_task = self.sentiment_bot.analyze_sentiment(request.news_content)
        reasoning_task = self.reasoning_bot.explain_market_trend(news=aligned_context)

        sentiment_result, reasoning_result = await asyncio.gather(sentiment_task, reasoning_task)

        # 3. Save analysis result to database
        await self.repo.save_analysis_result(
            news_id=request.news_id,
            sentiment=sentiment_result.label,
            confidence=sentiment_result.score,
            trend=reasoning_result.trend,
            reasoning=reasoning_result.reasoning
        )

        # 4. Return response
        return AnalyzeNewsResponse(
            sentiment=sentiment_result.label,
            confidence=sentiment_result.score,
            trend=reasoning_result.trend,
            reasoning=reasoning_result.reasoning
        )