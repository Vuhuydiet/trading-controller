import json
import logging
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.modules.news.domain.article import NewsArticle, NewsInsight
from app.shared.core.config import settings

logger = logging.getLogger(__name__)


class KafkaNewsProducer:
    """Kafka producer for publishing news articles and insights"""

    def __init__(self):
        self._producer: Optional[KafkaProducer] = None
        self._articles_topic = settings.KAFKA_NEWS_ARTICLES_TOPIC
        self._insights_topic = settings.KAFKA_NEWS_INSIGHTS_TOPIC

    def start(self):
        """Initialize and start the Kafka producer"""
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
            )
            logger.info(
                f"Kafka producer started. Bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}"
            )
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {str(e)}")
            raise

    def stop(self):
        """Stop the Kafka producer"""
        if self._producer:
            self._producer.close()
            logger.info("Kafka producer stopped")

    def produce_article(self, article: NewsArticle) -> bool:
        """Publish a news article to Kafka"""
        if not self._producer:
            logger.error("Kafka producer not started")
            return False

        try:
            # Handle both enum and string (due to use_enum_values=True in Pydantic)
            source = article.source.value if hasattr(article.source, 'value') else article.source

            article_dict = {
                "source": source,
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "content": article.content,
                "author": article.author,
            }

            # Use URL as key for partitioning (same article always goes to same partition)
            self._producer.send(
                topic=self._articles_topic,
                key=article.url,
                value=article_dict,
            )
            self._producer.flush()

            logger.info(f"Published article to Kafka: {article.title}")
            return True

        except KafkaError as e:
            logger.error(f"Failed to publish article to Kafka: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing article: {str(e)}")
            return False

    def produce_insight(self, insight: NewsInsight, article: NewsArticle) -> bool:
        """Publish a news insight to Kafka"""
        if not self._producer:
            logger.error("Kafka producer not started")
            return False

        try:
            insight_dict = {
                "article_url": article.url,
                "article_title": article.title,
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "key_points": insight.key_points,
                "market_impact": insight.market_impact,
                "affected_symbols": insight.affected_symbols,
                "confidence_score": insight.confidence_score,
                "generated_at": insight.generated_at.isoformat(),
            }

            # Use article URL as key to maintain ordering
            self._producer.send(
                topic=self._insights_topic,
                key=article.url,
                value=insight_dict,
            )
            self._producer.flush()

            logger.info(f"Published insight to Kafka for article: {article.title}")
            return True

        except KafkaError as e:
            logger.error(f"Failed to publish insight to Kafka: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing insight: {str(e)}")
            return False
