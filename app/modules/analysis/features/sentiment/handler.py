import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlmodel import Session, select

from .dtos import (
    SymbolSentimentResponse,
    MarketSentimentResponse,
    NewsSentimentResponse,
    SentimentData,
    SentimentBreakdown,
    SentimentFactor,
    AnalyzeSentimentNewsRequest,
)
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort
from app.modules.analysis.domain.entities import SymbolSentiment, AnalysisResult


class SentimentHandler:
    def __init__(
        self,
        sentiment_analyzer: SentimentAnalyzerPort,
        reasoner: MarketReasonerPort,
        session: Session,
    ):
        self.sentiment_analyzer = sentiment_analyzer
        self.reasoner = reasoner
        self.session = session

    async def get_symbol_sentiment(
        self, symbol: str, period: str = "24h"
    ) -> SymbolSentimentResponse:
        """Get sentiment analysis for a specific symbol"""

        # Check cache first
        cached = self._get_cached_sentiment(symbol, period)
        if cached:
            return cached

        # Generate new analysis using AI
        analysis_prompt = f"Analyze current market sentiment for {symbol} cryptocurrency over the last {period}."

        sentiment_result = await self.sentiment_analyzer.analyze_sentiment(analysis_prompt)
        reasoning_result = await self.reasoner.explain_market_trend(
            news=f"Market analysis for {symbol}",
            price_change=0
        )

        # Convert sentiment to score (-1 to 1)
        sentiment_score = self._label_to_score(sentiment_result.label, sentiment_result.score)
        sentiment_label = self._score_to_label(sentiment_score)

        # Generate mock breakdown based on sentiment
        breakdown = self._generate_breakdown(sentiment_score)

        # Extract factors from reasoning
        factors = self._extract_factors(reasoning_result.reasoning, reasoning_result.trend)

        # Save to database
        db_sentiment = SymbolSentiment(
            symbol=symbol,
            period=period,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=sentiment_result.score,
            positive_count=breakdown.positive,
            neutral_count=breakdown.neutral,
            negative_count=breakdown.negative,
        )
        self.session.add(db_sentiment)
        self.session.commit()

        return SymbolSentimentResponse(
            symbol=symbol,
            period=period,
            sentiment=SentimentData(
                score=round(sentiment_score, 2),
                label=sentiment_label,
                confidence=round(sentiment_result.score, 2),
            ),
            breakdown=breakdown,
            top_factors=factors,
            analyzed_at=datetime.now(timezone.utc),
        )

    async def get_market_sentiment(self, period: str = "24h") -> MarketSentimentResponse:
        """Get overall market sentiment"""

        # Analyze overall crypto market
        analysis_prompt = f"Analyze the overall cryptocurrency market sentiment over the last {period}."

        sentiment_result = await self.sentiment_analyzer.analyze_sentiment(analysis_prompt)

        sentiment_score = self._label_to_score(sentiment_result.label, sentiment_result.score)
        sentiment_label = self._score_to_label(sentiment_score)
        breakdown = self._generate_breakdown(sentiment_score)

        # Top movers (could be fetched from market data in production)
        top_movers = [
            {"symbol": "BTCUSDT", "sentiment": "BULLISH", "change": "+2.5%"},
            {"symbol": "ETHUSDT", "sentiment": "BULLISH", "change": "+3.1%"},
            {"symbol": "SOLUSDT", "sentiment": "NEUTRAL", "change": "+0.8%"},
        ]

        return MarketSentimentResponse(
            period=period,
            overall_sentiment=SentimentData(
                score=round(sentiment_score, 2),
                label=sentiment_label,
                confidence=round(sentiment_result.score, 2),
            ),
            breakdown=breakdown,
            top_movers=top_movers,
            analyzed_at=datetime.now(timezone.utc),
        )

    async def analyze_news_sentiment(
        self, request: AnalyzeSentimentNewsRequest
    ) -> NewsSentimentResponse:
        """Analyze sentiment of specific news content"""

        sentiment_result = await self.sentiment_analyzer.analyze_sentiment(request.news_content)

        sentiment_score = self._label_to_score(sentiment_result.label, sentiment_result.score)
        sentiment_label = self._score_to_label(sentiment_score)

        # Extract key phrases (simple extraction)
        key_phrases = self._extract_key_phrases(request.news_content)

        # Detect affected symbols
        affected_symbols = self._detect_symbols(request.news_content)
        if request.symbol and request.symbol not in affected_symbols:
            affected_symbols.insert(0, request.symbol)

        return NewsSentimentResponse(
            sentiment=SentimentData(
                score=round(sentiment_score, 2),
                label=sentiment_label,
                confidence=round(sentiment_result.score, 2),
            ),
            key_phrases=key_phrases[:5],
            affected_symbols=affected_symbols[:5],
            analyzed_at=datetime.now(timezone.utc),
        )

    def _get_cached_sentiment(
        self, symbol: str, period: str
    ) -> Optional[SymbolSentimentResponse]:
        """Get cached sentiment if fresh enough"""
        cache_duration = {
            "1h": timedelta(minutes=15),
            "4h": timedelta(hours=1),
            "24h": timedelta(hours=4),
            "7d": timedelta(hours=12),
        }

        max_age = cache_duration.get(period, timedelta(hours=4))
        cutoff = datetime.now(timezone.utc) - max_age

        statement = (
            select(SymbolSentiment)
            .where(SymbolSentiment.symbol == symbol)
            .where(SymbolSentiment.period == period)
            .where(SymbolSentiment.analyzed_at > cutoff)
            .order_by(SymbolSentiment.analyzed_at.desc())
        )

        result = self.session.exec(statement).first()

        if result:
            return SymbolSentimentResponse(
                symbol=result.symbol,
                period=result.period,
                sentiment=SentimentData(
                    score=result.sentiment_score,
                    label=result.sentiment_label,
                    confidence=result.confidence,
                ),
                breakdown=SentimentBreakdown(
                    positive=result.positive_count,
                    neutral=result.neutral_count,
                    negative=result.negative_count,
                ),
                top_factors=[],  # Factors not cached
                analyzed_at=result.analyzed_at,
            )
        return None

    def _label_to_score(self, label: str, confidence: float) -> float:
        """Convert sentiment label to score (-1 to 1)"""
        label_lower = label.lower()
        if label_lower in ["positive", "bullish"]:
            return confidence * 0.5 + 0.5  # 0.5 to 1.0
        elif label_lower in ["negative", "bearish"]:
            return -confidence * 0.5 - 0.5  # -0.5 to -1.0
        else:
            return (confidence - 0.5) * 0.5  # -0.25 to 0.25

    def _score_to_label(self, score: float) -> str:
        """Convert score to sentiment label"""
        if score > 0.2:
            return "BULLISH"
        elif score < -0.2:
            return "BEARISH"
        return "NEUTRAL"

    def _generate_breakdown(self, score: float) -> SentimentBreakdown:
        """Generate sentiment breakdown based on score"""
        total = 100
        if score > 0.2:
            positive = int(40 + score * 30)
            negative = int(20 - score * 10)
        elif score < -0.2:
            positive = int(20 + score * 10)
            negative = int(40 - score * 30)
        else:
            positive = 35
            negative = 30

        neutral = total - positive - negative
        return SentimentBreakdown(positive=positive, neutral=neutral, negative=negative)

    def _extract_factors(self, reasoning: str, trend: str) -> List[SentimentFactor]:
        """Extract sentiment factors from AI reasoning"""
        factors = []

        # Simple factor extraction based on reasoning keywords
        if "etf" in reasoning.lower():
            factors.append(SentimentFactor(
                factor="ETF-related news",
                impact="POSITIVE" if trend == "UP" else "NEGATIVE",
                weight=0.35
            ))
        if "regulation" in reasoning.lower() or "regulatory" in reasoning.lower():
            factors.append(SentimentFactor(
                factor="Regulatory developments",
                impact="NEGATIVE" if "concern" in reasoning.lower() else "NEUTRAL",
                weight=0.25
            ))
        if "adoption" in reasoning.lower() or "institutional" in reasoning.lower():
            factors.append(SentimentFactor(
                factor="Institutional adoption",
                impact="POSITIVE",
                weight=0.30
            ))

        # Default factor if none found
        if not factors:
            factors.append(SentimentFactor(
                factor="Market momentum",
                impact="POSITIVE" if trend == "UP" else ("NEGATIVE" if trend == "DOWN" else "NEUTRAL"),
                weight=0.40
            ))

        return factors

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple keyword extraction
        keywords = ["bitcoin", "ethereum", "crypto", "market", "price", "surge",
                   "drop", "rally", "crash", "bullish", "bearish", "etf", "sec"]

        phrases = []
        words = text.lower().split()
        for i, word in enumerate(words):
            for keyword in keywords:
                if keyword in word:
                    # Get surrounding context
                    start = max(0, i - 2)
                    end = min(len(words), i + 3)
                    phrase = " ".join(words[start:end])
                    if phrase not in phrases:
                        phrases.append(phrase)
                    break

        return phrases[:5]

    def _detect_symbols(self, text: str) -> List[str]:
        """Detect cryptocurrency symbols in text"""
        symbol_map = {
            "bitcoin": "BTCUSDT",
            "btc": "BTCUSDT",
            "ethereum": "ETHUSDT",
            "eth": "ETHUSDT",
            "solana": "SOLUSDT",
            "sol": "SOLUSDT",
            "xrp": "XRPUSDT",
            "ripple": "XRPUSDT",
            "dogecoin": "DOGEUSDT",
            "doge": "DOGEUSDT",
            "cardano": "ADAUSDT",
            "ada": "ADAUSDT",
        }

        text_lower = text.lower()
        detected = []
        for keyword, symbol in symbol_map.items():
            if keyword in text_lower and symbol not in detected:
                detected.append(symbol)

        return detected
