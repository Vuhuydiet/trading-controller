import logging
from typing import Any, List, Optional

from bson.objectid import ObjectId  # type: ignore[import-not-found]

from app.modules.news.domain.article import (
    NewsArticle,
    NewsInsight,
    NewsSource,
)
from app.modules.news.domain.ports import InsightRepository, NewsRepository
from app.shared.core.config import settings

logger = logging.getLogger(__name__)


class MongoNewsRepository(NewsRepository):
    """MongoDB implementation of NewsRepository"""

    def __init__(self, db: Any):  # type: ignore[no-untyped-def]
        self.db = db
        self.collection = db[settings.NEWS_COLLECTION]

    async def save_article(self, article: NewsArticle) -> str:
        """Save article to MongoDB"""
        try:
            article_dict = article.model_dump()
            article_dict["source"] = article.source.value
            article_dict["status"] = article.status.value

            result = await self.collection.insert_one(article_dict)
            logger.info(f"Saved article: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving article: {str(e)}")
            raise

    async def get_article(self, article_id: str) -> Optional[NewsArticle]:
        """Get article by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(article_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                return NewsArticle(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting article: {str(e)}")
            return None

    async def get_articles_by_source(
        self, source: NewsSource, limit: int = 50, skip: int = 0
    ) -> List[NewsArticle]:
        """Get articles from a specific source"""
        try:
            source_val = source.value
            cursor = (
                self.collection.find({"source": source_val})
                .sort("published_date", -1)
                .skip(skip)
                .limit(limit)
            )
            articles = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                articles.append(NewsArticle(**doc))
            return articles
        except Exception as e:
            logger.error(f"Error getting articles by source: {str(e)}")
            return []

    async def get_recent_articles(self, limit: int = 100) -> List[NewsArticle]:
        """Get recent articles from all sources"""
        try:
            cursor = self.collection.find().sort("published_date", -1).limit(limit)
            articles = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                articles.append(NewsArticle(**doc))
            return articles
        except Exception as e:
            logger.error(f"Error getting recent articles: {str(e)}")
            return []

    async def article_exists(self, url: str) -> bool:
        """Check if article URL already exists"""
        try:
            count = await self.collection.count_documents({"url": url})
            return bool(count > 0)
        except Exception as e:
            logger.error(f"Error checking article existence: {str(e)}")
            return False


class MongoInsightRepository(InsightRepository):
    """MongoDB implementation of InsightRepository"""

    def __init__(self, db: Any):  # type: ignore[no-untyped-def]
        self.db = db
        self.collection = db[settings.INSIGHTS_COLLECTION]

    async def save_insight(self, insight: NewsInsight) -> str:
        """Save insight to MongoDB"""
        try:
            insight_dict = insight.model_dump()
            insight_dict["source"] = insight.source.value

            result = await self.collection.insert_one(insight_dict)
            logger.info(f"Saved insight: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving insight: {str(e)}")
            raise

    async def get_insight(self, insight_id: str) -> Optional[NewsInsight]:
        """Get insight by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(insight_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                return NewsInsight(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting insight: {str(e)}")
            return None

    async def get_insights_by_article(self, article_id: str) -> Optional[NewsInsight]:
        """Get insight for an article"""
        try:
            doc = await self.collection.find_one({"article_id": article_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return NewsInsight(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting insight by article: {str(e)}")
            return None

    async def get_recent_insights(self, limit: int = 50) -> List[NewsInsight]:
        """Get recent insights"""
        try:
            cursor = self.collection.find().sort("processed_date", -1).limit(limit)
            insights = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                insights.append(NewsInsight(**doc))
            return insights
        except Exception as e:
            logger.error(f"Error getting recent insights: {str(e)}")
            return []
