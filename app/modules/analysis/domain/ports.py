from abc import ABC, abstractmethod
from typing import Dict, Any

# 1. Interface cho Sentiment Analysis
class SentimentAnalyzerPort(ABC):
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Output mong đợi: {'label': 'positive', 'score': 0.9}"""
        pass

# 2. Interface cho Causal Reasoning
class MarketReasonerPort(ABC):
    @abstractmethod
    async def explain_market_trend(self, news: str, price_change: float) -> str:
        """Output mong đợi: Chuỗi text giải thích"""
        pass

# 3. Interface cho Repository (Lưu kết quả)
class AnalysisRepositoryPort(ABC):
    @abstractmethod
    async def save_analysis_result(self, news_id: str, sentiment: str, reasoning: str) -> bool:
        pass