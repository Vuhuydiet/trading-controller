from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

class SentimentLabel(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TrendDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


# Database Table for Analysis Results
class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: str = Field(foreign_key="analysis_cached_news.news_id", index=True)
    sentiment: str
    confidence: float
    trend: str = Field(default="NEUTRAL")
    reasoning: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    news: Optional["CachedNews"] = Relationship(back_populates="analysis")

# Database Table for Symbol Sentiment Analysis
class SymbolSentiment(SQLModel, table=True):
    __tablename__ = "symbol_sentiments"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    period: str  # 1h, 4h, 24h, 7d
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float
    positive_count: int = Field(default=0)
    neutral_count: int = Field(default=0)
    negative_count: int = Field(default=0)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Database Table for Trend Predictions
class TrendPrediction(SQLModel, table=True):
    __tablename__ = "trend_predictions"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    timeframe: str  # 1h, 4h, 24h, 7d
    current_price: str
    direction: str  # UP, DOWN, NEUTRAL
    confidence: float
    target_low: str
    target_mid: str
    target_high: str
    support_levels: str  # JSON string
    resistance_levels: str  # JSON string
    model_version: str = Field(default="v1.0.0")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Database Table for Causal Analysis
class CausalAnalysis(SQLModel, table=True):
    __tablename__ = "causal_analyses"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    period_from: datetime
    period_to: datetime
    price_from: str
    price_to: str
    price_change_percent: str
    causal_factors: str  # JSON string
    summary: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Database Table for Prediction History (for accuracy tracking)
class PredictionHistory(SQLModel, table=True):
    __tablename__ = "prediction_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    predicted_direction: str
    predicted_at: datetime
    target_price: str
    actual_price: Optional[str] = None
    actual_direction: Optional[str] = None
    is_correct: Optional[bool] = None
    verified_at: Optional[datetime] = None



# 👇 Bảng mới để lưu tin tức nhận từ Kafka
class CachedNews(SQLModel, table=True):
    __tablename__ = "analysis_cached_news"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: str = Field(unique=True, index=True) # URL hoặc ID từ Crawler
    title: str
    source: str
    content: str # Lưu tóm tắt hoặc full text tùy bạn
    published_at: datetime

    analysis: Optional["AnalysisResult"] = Relationship(
        back_populates="news",
        sa_relationship_kwargs={"uselist": False} # 1-1 Relationship
    )