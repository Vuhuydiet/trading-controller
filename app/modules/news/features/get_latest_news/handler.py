import logging
from typing import List, Optional

from app.modules.news.domain.article import NewsSource
from app.modules.news.domain.services import NewsService
from app.modules.news.features.get_latest_news.dtos import NewsArticleResponse

logger = logging.getLogger(__name__)


class GetLatestNewsHandler:
    """Handler for retrieving latest news"""

    def __init__(self, news_service: NewsService):
        self.news_service = news_service

    async def handle(
        self,
        source: Optional[NewsSource] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[List[NewsArticleResponse], int]:
        """Get latest news articles"""
        try:
            if source:
                articles = await self.news_service.get_news_by_source(
                    source, limit=limit, skip=skip
                )
            else:
                articles = await self.news_service.get_recent_news(limit=limit)

            # Convert to response DTOs
            responses = [
                NewsArticleResponse(
                    id=article.id,
                    source=(
                        article.source.value if hasattr(article.source, "value") else article.source
                    ),
                    title=article.title,
                    content=article.content,
                    url=article.url,
                    author=article.author,
                    published_date=article.published_date,
                    crawled_date=article.crawled_date,
                    image_url=article.image_url,
                    metadata=article.metadata,
                )
                for article in articles
            ]

            return responses, len(responses)
        except Exception as e:
            logger.error(f"Error getting latest news: {str(e)}")
            raise
