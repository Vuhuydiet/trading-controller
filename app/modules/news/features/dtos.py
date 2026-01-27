"""DTOs for News API endpoints"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NewsAnalysisResponse(BaseModel):
    """Analysis data embedded in news response"""
    sentiment: str = Field(..., description="Sentiment: BULLISH, BEARISH, NEUTRAL")
    confidence: float = Field(..., description="Confidence score 0-1")
    trend: str = Field(..., description="Trend direction")
    reasoning: Optional[str] = Field(default=None, description="AI reasoning")


class NewsItemResponse(BaseModel):
    """Single news item response"""
    id: str = Field(..., description="News unique identifier")
    title: str = Field(..., description="News title")
    source: str = Field(..., description="News source")
    url: str = Field(..., description="Original article URL")
    content: str = Field(..., description="News content/summary")
    published_at: datetime = Field(..., description="Publication date")
    analysis: Optional[NewsAnalysisResponse] = Field(
        default=None, description="AI analysis if available"
    )

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    """Paginated news list response"""
    items: List[NewsItemResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total news count")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Has more pages")


class NewsDetailResponse(BaseModel):
    """Detailed news response with full insight"""
    id: str = Field(..., description="News unique identifier")
    title: str = Field(..., description="News title")
    source: str = Field(..., description="News source")
    url: str = Field(..., description="Original article URL")
    content: str = Field(..., description="Full news content")
    published_at: datetime = Field(..., description="Publication date")
    analysis: Optional[NewsAnalysisResponse] = Field(
        default=None, description="AI analysis"
    )
    related_symbols: List[str] = Field(
        default_factory=list, description="Related cryptocurrency symbols"
    )


class NewsSearchRequest(BaseModel):
    """Search request parameters"""
    q: str = Field(..., min_length=2, description="Search query")
    source: Optional[str] = Field(default=None, description="Filter by source")
    from_date: Optional[datetime] = Field(default=None, description="From date")
    to_date: Optional[datetime] = Field(default=None, description="To date")


class NewsBySymbolResponse(BaseModel):
    """News filtered by symbol"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    items: List[NewsItemResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total matching news")
