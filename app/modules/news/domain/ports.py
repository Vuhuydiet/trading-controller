from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.news.domain.article import NewsArticle, NewsInsight


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
