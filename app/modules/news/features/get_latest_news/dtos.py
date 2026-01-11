from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.news.domain.article import NewsSource


class GetLatestNewsRequest(BaseModel):
    """Request model for getting latest news"""

    source: Optional[NewsSource] = Field(default=None, description="Filter by news source")
    limit: int = Field(default=50, ge=1, le=100, description="Number of articles")
    skip: int = Field(default=0, ge=0, description="Skip offset")


class NewsArticleResponse(BaseModel):
    """Response model for news articles"""

    id: Optional[str] = Field(default=None)
    source: str
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_date: datetime
    crawled_date: datetime
    image_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class GetLatestNewsResponse(BaseModel):
    """Response model for latest news endpoint"""

    articles: List[NewsArticleResponse]
    total: int = Field(description="Total articles returned")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
