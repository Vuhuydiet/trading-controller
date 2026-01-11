from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.news.domain.article import NewsSource
from app.modules.news.domain.services import NewsService
from app.modules.news.features.get_insights.dtos import (
    GetInsightsResponse,
    InsightResponse,
)
from app.modules.news.features.get_insights.handler import GetInsightsHandler
from app.modules.news.infrastructure.crawlers import (
    BloombergCrawler,
    CoinDeskCrawler,
    ReutersCrawler,
    TwitterCrawler,
)
from app.modules.news.infrastructure.llm_adapter import get_llm_adapter
from app.modules.news.infrastructure.mongo_connection import get_mongodb
from app.modules.news.infrastructure.repository import (
    MongoInsightRepository,
    MongoNewsRepository,
)

router = APIRouter()


async def get_insights_handler() -> GetInsightsHandler:
    """Dependency injection for insights handler"""
    db = await get_mongodb()
    news_repo = MongoNewsRepository(db)
    insight_repo = MongoInsightRepository(db)

    crawlers = {
        NewsSource.COINDESK: CoinDeskCrawler(),
        NewsSource.REUTERS: ReutersCrawler(),
        NewsSource.BLOOMBERG: BloombergCrawler(),
        NewsSource.TWITTER: TwitterCrawler(),
    }

    llm_adapter = get_llm_adapter()
    news_service = NewsService(news_repo, insight_repo, crawlers, llm_adapter)

    return GetInsightsHandler(news_service)


@router.get(
    "/insights",
    response_model=GetInsightsResponse,
    summary="Get Latest News Insights",
    description="Retrieve AI-generated insights from recent news articles",
)
async def get_recent_insights(
    limit: int = Query(50, ge=1, le=100, description="Number of insights to return"),
    handler: GetInsightsHandler = Depends(get_insights_handler),
):
    """
    Get recent AI-generated insights from news articles.

    **Query Parameters:**
    - `limit`: Maximum insights to return (1-100, default 50)

    **Returns:**
    - List of insights with sentiment analysis, key points, and market impact
    - Timestamp of when the response was generated
    """
    try:
        insights, total = await handler.get_recent_insights(limit=limit)

        return GetInsightsResponse(
            insights=insights,
            total=total,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception:
        return GetInsightsResponse(
            insights=[],
            total=0,
            timestamp=datetime.now(timezone.utc),
        )


@router.get(
    "/insights/{article_id}",
    response_model=InsightResponse,
    summary="Get Insight for Article",
    description="Retrieve AI-generated insight for a specific article",
)
async def get_insight_by_article(
    article_id: str = Query(..., description="Article ID from MongoDB"),
    handler: GetInsightsHandler = Depends(get_insights_handler),
):
    """
    Get AI-generated insight for a specific article.

    **Path Parameters:**
    - `article_id`: The MongoDB ObjectId of the article

    **Returns:**
    - Detailed insight with sentiment analysis, key points, entities, and market impact
    """
    try:
        insight = await handler.get_insight_by_article(article_id)

        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found for this article")

        return insight
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error retrieving insight")
