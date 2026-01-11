from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.modules.news.domain.article import NewsSource
from app.modules.news.domain.ports import NewsCrawler
from app.modules.news.domain.services import NewsService
from app.modules.news.features.get_latest_news.dtos import GetLatestNewsResponse
from app.modules.news.features.get_latest_news.handler import GetLatestNewsHandler
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


async def get_news_handler() -> GetLatestNewsHandler:
    """Dependency injection for news handler"""
    db = await get_mongodb()
    news_repo = MongoNewsRepository(db)
    insight_repo = MongoInsightRepository(db)

    crawlers: Dict[NewsSource, NewsCrawler] = {
        NewsSource.COINDESK: CoinDeskCrawler(),
        NewsSource.REUTERS: ReutersCrawler(),
        NewsSource.BLOOMBERG: BloombergCrawler(),
        NewsSource.TWITTER: TwitterCrawler(),
    }

    llm_adapter = get_llm_adapter()
    news_service = NewsService(news_repo, insight_repo, crawlers, llm_adapter)

    return GetLatestNewsHandler(news_service)


@router.get(
    "/latest-news",
    response_model=GetLatestNewsResponse,
    summary="Get Latest Cryptocurrency News",
    description="Retrieve the latest cryptocurrency news articles from multiple sources",
)
async def get_latest_news(
    source: Optional[str] = Query(
        None, description="Filter by source: coindesk, reuters, bloomberg, twitter"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of articles to return"),
    skip: int = Query(0, ge=0, description="Number of articles to skip"),
    handler: GetLatestNewsHandler = Depends(get_news_handler),
):
    """
    Get the latest cryptocurrency news articles.

    **Query Parameters:**
    - `source`: Optional filter by news source (coindesk, reuters, bloomberg, twitter)
    - `limit`: Maximum articles to return (1-100, default 50)
    - `skip`: Offset for pagination (default 0)

    **Returns:**
    - List of news articles with metadata
    - Timestamp of when the response was generated
    """
    try:
        # Convert string source to enum if provided
        source_enum = None
        if source:
            try:
                source_enum = NewsSource(source.lower())
            except ValueError:
                pass

        articles, total = await handler.handle(source=source_enum, limit=limit, skip=skip)

        return GetLatestNewsResponse(
            articles=articles,
            total=total,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception:
        return GetLatestNewsResponse(
            articles=[],
            total=0,
            timestamp=datetime.now(timezone.utc),
        )
