from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field

# Output Models for Type Safety
class SentimentResult(BaseModel):
    """Standardized sentiment analysis output"""
    label: str = Field(..., description="Sentiment label: positive, negative, or neutral")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")

class ReasoningResult(BaseModel):
    """Standardized market reasoning output"""
    trend: str = Field(..., description="Predicted trend: UP, DOWN, or NEUTRAL")
    reasoning: str = Field(..., description="Explanation for the trend prediction")

# 1. Interface cho Sentiment Analysis
class SentimentAnalyzerPort(ABC):
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.

        Args:
            text: Input text to analyze

        Returns:
            SentimentResult with label and confidence score
        """
        pass

# 2. Interface cho Causal Reasoning
class MarketReasonerPort(ABC):
    @abstractmethod
    async def explain_market_trend(self, news: str, price_change: float = 0) -> ReasoningResult:
        """
        Explain market trend based on news and price movement.

        Args:
            news: News content or aligned context
            price_change: Price change percentage (optional)

        Returns:
            ReasoningResult with trend prediction and reasoning
        """
        pass

# 3. Interface cho Repository (Lưu kết quả)
class AnalysisRepositoryPort(ABC):
    @abstractmethod
    async def save_analysis_result(
        self,
        news_id: str,
        sentiment: str,
        confidence: float,
        trend: str,
        reasoning: str
    ) -> bool:
        """Save analysis result to database"""
        pass