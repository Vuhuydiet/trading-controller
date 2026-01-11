import logging
from typing import Any, Dict, List, Optional

from app.modules.news.domain.article import NewsArticle, NewsInsight, NewsSource
from app.modules.news.domain.ports import (
    InsightRepository,
    LLMAdapter,
    NewsCrawler,
    NewsRepository,
)

logger = logging.getLogger(__name__)


class NewsService:
    """Business logic for news management"""

    def __init__(
        self,
        news_repo: NewsRepository,
        insight_repo: InsightRepository,
        crawlers: dict[NewsSource, NewsCrawler],
        llm_adapter: LLMAdapter,
    ):
        self.news_repo = news_repo
        self.insight_repo = insight_repo
        self.crawlers = crawlers
        self.llm_adapter = llm_adapter

    async def crawl_and_process_news(self) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
        """Main pipeline: crawl news, parse with LLM, store insights"""
        results: Dict[str, Any] = {
            "crawled": 0,
            "processed": 0,
            "failed": 0,
            "errors": [],
        }

        try:
            # Crawl news from all sources
            all_articles: list[Any] = []
            for source, crawler in self.crawlers.items():
                try:
                    logger.info(f"Crawling news from {source}...")
                    articles = await crawler.fetch_news()
                    all_articles.extend(articles)
                    logger.info(f"Found {len(articles)} articles from {source}")
                except Exception as e:
                    logger.error(f"Error crawling {source}: {str(e)}")
                    results["errors"].append(f"Crawler error for {source}: {str(e)}")

            results["crawled"] = len(all_articles)

            # Save and process articles
            for article in all_articles:
                try:
                    # Check if article already exists
                    if await self.news_repo.article_exists(article.url):
                        logger.debug(f"Article already exists: {article.url}")
                        continue

                    # Save article
                    article_id = await self.news_repo.save_article(article)
                    logger.info(f"Saved article: {article_id}")

                    # Generate insight using LLM
                    try:
                        insight = await self.llm_adapter.parse_article_to_insight(article)
                        insight.article_id = article_id
                        insight_id = await self.insight_repo.save_insight(insight)
                        logger.info(f"Generated insight: {insight_id}")
                        results["processed"] += 1
                    except Exception as e:
                        logger.error(f"Error generating insight for article {article_id}: {str(e)}")
                        results["errors"].append(f"LLM processing error: {str(e)}")
                        results["failed"] += 1

                except Exception as e:
                    logger.error(f"Error processing article: {str(e)}")
                    results["errors"].append(f"Article processing error: {str(e)}")
                    results["failed"] += 1

            logger.info(f"Pipeline completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Crawl and process pipeline failed: {str(e)}")
            results["errors"].append(f"Pipeline error: {str(e)}")
            return results

    async def get_recent_news(self, limit: int = 50) -> List[NewsArticle]:
        """Get recent news articles"""
        return await self.news_repo.get_recent_articles(limit=limit)

    async def get_news_by_source(
        self, source: NewsSource, limit: int = 50, skip: int = 0
    ) -> List[NewsArticle]:
        """Get news filtered by source"""
        return await self.news_repo.get_articles_by_source(source, limit=limit, skip=skip)

    async def get_insights_for_article(self, article_id: str) -> Optional[NewsInsight]:
        """Get AI insight for a specific article"""
        return await self.insight_repo.get_insights_by_article(article_id)

    async def get_recent_insights(self, limit: int = 50) -> List[NewsInsight]:
        """Get recent insights"""
        return await self.insight_repo.get_recent_insights(limit=limit)
