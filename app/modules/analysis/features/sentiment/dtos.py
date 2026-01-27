from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Request DTOs
class AnalyzeSentimentNewsRequest(BaseModel):
    news_content: str = Field(..., description="News content to analyze")
    symbol: Optional[str] = Field(default=None, description="Related symbol (optional)")


# Response DTOs
class SentimentBreakdown(BaseModel):
    positive: int
    neutral: int
    negative: int


class SentimentFactor(BaseModel):
    factor: str
    impact: str  # POSITIVE, NEGATIVE, NEUTRAL
    weight: float


class SentimentData(BaseModel):
    score: float = Field(..., ge=-1.0, le=1.0)
    label: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float = Field(..., ge=0.0, le=1.0)


class SymbolSentimentResponse(BaseModel):
    symbol: str
    period: str
    sentiment: SentimentData
    breakdown: SentimentBreakdown
    top_factors: List[SentimentFactor]
    analyzed_at: datetime


class MarketSentimentResponse(BaseModel):
    period: str
    overall_sentiment: SentimentData
    breakdown: SentimentBreakdown
    top_movers: List[dict]  # [{"symbol": "BTCUSDT", "sentiment": "BULLISH", "change": "+5%"}]
    analyzed_at: datetime


class NewsSentimentResponse(BaseModel):
    sentiment: SentimentData
    key_phrases: List[str]
    affected_symbols: List[str]
    analyzed_at: datetime
