import logging
from typing import List, Optional

from app.modules.news.domain.services import NewsService
from app.modules.news.features.get_insights.dtos import InsightResponse

logger = logging.getLogger(__name__)


class GetInsightsHandler:
    """Handler for retrieving insights"""

    def __init__(self, news_service: NewsService):
        self.news_service = news_service

    async def get_recent_insights(self, limit: int = 50) -> tuple[List[InsightResponse], int]:
        """Get recent insights"""
        try:
            insights = await self.news_service.get_recent_insights(limit=limit)

            responses = [
                InsightResponse(
                    id=insight.id,
                    article_id=insight.article_id,
                    source=(
                        insight.source.value if hasattr(insight.source, "value") else insight.source
                    ),
                    cryptocurrency_mentioned=insight.cryptocurrency_mentioned,
                    sentiment=insight.sentiment,
                    sentiment_score=insight.sentiment_score,
                    key_points=insight.key_points,
                    market_impact=insight.market_impact,
                    entities=insight.entities,
                    tags=insight.tags,
                    summary=insight.summary,
                    processed_date=insight.processed_date,
                    llm_model_used=insight.llm_model_used,
                )
                for insight in insights
            ]

            return responses, len(responses)
        except Exception as e:
            logger.error(f"Error getting recent insights: {str(e)}")
            raise

    async def get_insight_by_article(self, article_id: str) -> Optional[InsightResponse]:
        """Get insight for a specific article"""
        try:
            insight = await self.news_service.get_insights_for_article(article_id)

            if not insight:
                return None

            return InsightResponse(
                id=insight.id,
                article_id=insight.article_id,
                source=(
                    insight.source.value if hasattr(insight.source, "value") else insight.source
                ),
                cryptocurrency_mentioned=insight.cryptocurrency_mentioned,
                sentiment=insight.sentiment,
                sentiment_score=insight.sentiment_score,
                key_points=insight.key_points,
                market_impact=insight.market_impact,
                entities=insight.entities,
                tags=insight.tags,
                summary=insight.summary,
                processed_date=insight.processed_date,
                llm_model_used=insight.llm_model_used,
            )
        except Exception as e:
            logger.error(f"Error getting insight by article: {str(e)}")
            raise
