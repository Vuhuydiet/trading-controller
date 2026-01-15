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


class NewsArticle(BaseModel):
    """Domain model for news articles"""

    source: NewsSource = Field(..., description="News source")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content/body")
    url: str = Field(..., description="Article URL")
    author: Optional[str] = Field(default=None, description="Article author")
    published_at: datetime = Field(..., description="Publication date")

    class Config:
        use_enum_values = True


class NewsInsight(BaseModel):
    """Domain model for AI-generated insights from news"""

    summary: str = Field(..., description="Brief summary of the article")
    sentiment: str = Field(..., description="Sentiment: bullish, bearish, neutral")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    market_impact: Optional[str] = Field(default=None, description="Predicted market impact")
    affected_symbols: List[str] = Field(
        default_factory=list, description="Affected cryptocurrency symbols"
    )
    confidence_score: float = Field(default=0.0, description="Confidence score (0 to 1)")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When insight was generated",
    )

    class Config:
        use_enum_values = True
