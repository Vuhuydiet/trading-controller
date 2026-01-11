from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.news.domain.article import NewsArticle, NewsInsight, NewsSource


class NewsRepository(ABC):
    """Port for news article persistence"""

    @abstractmethod
    async def save_article(self, article: NewsArticle) -> str:
        """Save a news article and return its ID"""
        pass

    @abstractmethod
    async def get_article(self, article_id: str) -> Optional[NewsArticle]:
        """Get article by ID"""
        pass

    @abstractmethod
    async def get_articles_by_source(
        self, source: NewsSource, limit: int = 50, skip: int = 0
    ) -> List[NewsArticle]:
        """Get articles from a specific source"""
        pass

    @abstractmethod
    async def get_recent_articles(self, limit: int = 100) -> List[NewsArticle]:
        """Get recent articles from all sources"""
        pass

    @abstractmethod
    async def article_exists(self, url: str) -> bool:
        """Check if article URL already exists"""
        pass


class InsightRepository(ABC):
    """Port for news insight persistence"""

    @abstractmethod
    async def save_insight(self, insight: NewsInsight) -> str:
        """Save insight and return its ID"""
        pass

    @abstractmethod
    async def get_insight(self, insight_id: str) -> Optional[NewsInsight]:
        """Get insight by ID"""
        pass

    @abstractmethod
    async def get_insights_by_article(self, article_id: str) -> Optional[NewsInsight]:
        """Get insight for an article"""
        pass

    @abstractmethod
    async def get_recent_insights(self, limit: int = 50) -> List[NewsInsight]:
        """Get recent insights"""
        pass


class NewsCrawler(ABC):
    """Port for news crawling"""

    @abstractmethod
    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch news from the source"""
        pass

    @abstractmethod
    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single article from URL"""
        pass


class LLMAdapter(ABC):
    """Port for LLM integration"""

    @abstractmethod
    async def parse_article_to_insight(self, article: NewsArticle) -> NewsInsight:
        """Use LLM to parse article and generate insight"""
        pass
