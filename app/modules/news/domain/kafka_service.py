import logging
from typing import Any, Dict, List

from app.modules.news.domain.article import NewsArticle, NewsSource
from app.modules.news.domain.ports import LLMAdapter, NewsCrawler
from app.modules.news.infrastructure.kafka_producer import KafkaNewsProducer

logger = logging.getLogger(__name__)


class NewsKafkaService:
    """Business logic for news crawling and publishing to Kafka"""

    def __init__(
        self,
        kafka_producer: KafkaNewsProducer,
        crawlers: dict[NewsSource, NewsCrawler],
        llm_adapter: LLMAdapter,
    ):
        self.kafka_producer = kafka_producer
        self.crawlers = crawlers
        self.llm_adapter = llm_adapter
        self._seen_urls: set[str] = set()  # Simple in-memory deduplication

    async def crawl_and_publish_news(self) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
        """Main pipeline: crawl news, parse with LLM, publish to Kafka"""
        results: Dict[str, Any] = {
            "crawled": 0,
            "published_articles": 0,
            "published_insights": 0,
            "duplicates": 0,
            "failed": 0,
            "errors": [],
        }

        try:
            # Crawl news from all sources
            all_articles: List[NewsArticle] = []
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

            # Process and publish articles
            for article in all_articles:
                try:
                    # Check for duplicates
                    if article.url in self._seen_urls:
                        logger.debug(f"Duplicate article: {article.url}")
                        results["duplicates"] += 1
                        continue

                    # Publish article to Kafka
                    if self.kafka_producer.produce_article(article):
                        self._seen_urls.add(article.url)
                        results["published_articles"] += 1

                        # Generate insight using LLM
                        try:
                            insight = await self.llm_adapter.parse_article_to_insight(
                                article
                            )
                            # Publish insight to Kafka
                            if self.kafka_producer.produce_insight(insight, article):
                                results["published_insights"] += 1
                                logger.info(
                                    f"Published article and insight for: {article.title}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error generating insight for article {article.url}: {str(e)}"
                            )
                            results["errors"].append(f"LLM processing error: {str(e)}")
                            results["failed"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    logger.error(f"Error processing article: {str(e)}")
                    results["errors"].append(f"Article processing error: {str(e)}")
                    results["failed"] += 1

            logger.info(f"Pipeline completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Crawl and publish pipeline failed: {str(e)}")
            results["errors"].append(f"Pipeline error: {str(e)}")
            return results

    def clear_seen_urls(self):
        """Clear the in-memory deduplication cache"""
        self._seen_urls.clear()
        logger.info("Cleared seen URLs cache")
