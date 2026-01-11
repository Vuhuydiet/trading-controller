from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NewsSource(str, Enum):
    """Supported news sources"""

    COINDESK = "coindesk"
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    TWITTER = "twitter"


class ArticleStatus(str, Enum):
    """Status of article processing"""

    CRAWLED = "crawled"
    PROCESSED = "processed"
    FAILED = "failed"


class NewsArticle(BaseModel):
    """Domain model for news articles"""

    id: Optional[str] = Field(default=None, description="MongoDB ObjectId")
    source: NewsSource = Field(..., description="News source")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content/body")
    url: str = Field(..., description="Article URL")
    author: Optional[str] = Field(default=None, description="Article author")
    published_date: datetime = Field(..., description="Publication date")
    crawled_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date when article was crawled",
    )
    image_url: Optional[str] = Field(default=None, description="Article image URL")
    status: ArticleStatus = Field(default=ArticleStatus.CRAWLED, description="Processing status")
    raw_html: Optional[str] = Field(default=None, description="Raw HTML content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


class NewsInsight(BaseModel):
    """Domain model for AI-generated insights from news"""

    id: Optional[str] = Field(default=None, description="MongoDB ObjectId")
    article_id: str = Field(..., description="Reference to NewsArticle")
    source: NewsSource = Field(..., description="News source")
    cryptocurrency_mentioned: List[str] = Field(
        default_factory=list, description="Cryptocurrencies mentioned"
    )
    sentiment: str = Field(..., description="Sentiment: positive, negative, neutral")
    sentiment_score: float = Field(..., description="Sentiment score (-1 to 1)")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    market_impact: Optional[str] = Field(default=None, description="Predicted market impact")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Named entities extracted")
    tags: List[str] = Field(default_factory=list, description="Topic tags")
    summary: str = Field(..., description="Brief summary of the article")
    processed_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When insight was generated",
    )
    llm_model_used: str = Field(default="", description="LLM model used for processing")
    raw_analysis: Dict[str, Any] = Field(default_factory=dict, description="Raw LLM output")

    class Config:
        use_enum_values = True
