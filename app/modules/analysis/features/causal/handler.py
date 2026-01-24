import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlmodel import Session

from .dtos import (
    CausalAnalysisResponse,
    ExplainPriceRequest,
    ExplainPriceResponse,
    CausalFactor,
    PriceChange,
    Period,
)
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort
from app.modules.analysis.domain.entities import CausalAnalysis
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient


class CausalHandler:
    def __init__(
        self,
        sentiment_analyzer: SentimentAnalyzerPort,
        reasoner: MarketReasonerPort,
        session: Session,
    ):
        self.sentiment_analyzer = sentiment_analyzer
        self.reasoner = reasoner
        self.session = session
        self.binance_client = BinanceRestClient()

    async def get_causal_analysis(
        self,
        symbol: str,
        period_from: Optional[datetime] = None,
        period_to: Optional[datetime] = None,
    ) -> CausalAnalysisResponse:
        """Get causal reasoning for price movement"""

        # Default to last 24 hours if not specified
        if period_to is None:
            period_to = datetime.now(timezone.utc)
        if period_from is None:
            period_from = period_to - timedelta(hours=24)

        # Get price data from Binance
        price_from, price_to = await self._get_price_range(symbol, period_from, period_to)

        # Calculate price change
        price_from_float = float(price_from)
        price_to_float = float(price_to)
        if price_from_float > 0:
            change_pct = ((price_to_float - price_from_float) / price_from_float) * 100
        else:
            change_pct = 0

        change_str = f"+{change_pct:.1f}%" if change_pct >= 0 else f"{change_pct:.1f}%"

        # Create context for AI analysis
        context = f"""
        Analyze the causal factors for {symbol} price movement:
        - Period: {period_from.isoformat()} to {period_to.isoformat()}
        - Price moved from {price_from} to {price_to} ({change_str})

        Identify the main factors that caused this price movement.
        Consider: regulatory news, on-chain data, market sentiment, technical factors.
        """

        # Get AI reasoning
        reasoning_result = await self.reasoner.explain_market_trend(
            news=context,
            price_change=change_pct
        )

        # Extract causal factors from reasoning
        factors = self._extract_causal_factors(reasoning_result.reasoning, change_pct)

        # Generate summary
        summary = self._generate_summary(symbol, change_str, factors)

        # Save to database
        db_analysis = CausalAnalysis(
            symbol=symbol,
            period_from=period_from,
            period_to=period_to,
            price_from=price_from,
            price_to=price_to,
            price_change_percent=change_str,
            causal_factors=json.dumps([f.model_dump() for f in factors]),
            summary=summary,
        )
        self.session.add(db_analysis)
        self.session.commit()

        return CausalAnalysisResponse(
            symbol=symbol,
            period=Period(period_from=period_from, period_to=period_to),
            price_change=PriceChange(price_from=price_from, price_to=price_to, percent=change_str),
            causal_factors=factors,
            summary=summary,
            generated_at=datetime.now(timezone.utc),
        )

    async def explain_price_movement(
        self, request: ExplainPriceRequest
    ) -> ExplainPriceResponse:
        """Explain a specific price movement"""

        # Calculate price change
        price_from_float = float(request.price_from)
        price_to_float = float(request.price_to)
        if price_from_float > 0:
            change_pct = ((price_to_float - price_from_float) / price_from_float) * 100
        else:
            change_pct = 0

        change_str = f"+{change_pct:.1f}%" if change_pct >= 0 else f"{change_pct:.1f}%"

        # Create context for AI analysis
        context = f"""
        Explain why {request.symbol} price moved from {request.price_from} to {request.price_to} ({change_str}).
        Period: {request.period_from.isoformat()} to {request.period_to.isoformat()}
        """
        if request.additional_context:
            context += f"\nAdditional context: {request.additional_context}"

        # Get AI reasoning
        reasoning_result = await self.reasoner.explain_market_trend(
            news=context,
            price_change=change_pct
        )
        sentiment_result = await self.sentiment_analyzer.analyze_sentiment(context)

        # Extract causal factors
        factors = self._extract_causal_factors(reasoning_result.reasoning, change_pct)

        # Generate summary
        summary = self._generate_summary(request.symbol, change_str, factors)

        return ExplainPriceResponse(
            symbol=request.symbol,
            price_change=PriceChange(
                price_from=request.price_from,
                price_to=request.price_to,
                percent=change_str
            ),
            causal_factors=factors,
            summary=summary,
            confidence=round(sentiment_result.score, 2),
            generated_at=datetime.now(timezone.utc),
        )

    async def _get_price_range(
        self, symbol: str, period_from: datetime, period_to: datetime
    ) -> tuple[str, str]:
        """Get price at start and end of period"""
        try:
            # Get klines for the period
            start_ms = int(period_from.timestamp() * 1000)
            end_ms = int(period_to.timestamp() * 1000)

            klines = await self.binance_client.get_klines(
                symbol=symbol,
                interval="1h",
                start_time=start_ms,
                end_time=end_ms,
                limit=100
            )

            if klines and len(klines) > 0:
                # First kline open price
                price_from = klines[0][1]  # Open price
                # Last kline close price
                price_to = klines[-1][4]  # Close price
                return str(price_from), str(price_to)

            # Fallback to current price
            ticker = await self.binance_client.get_ticker_24hr(symbol)
            if isinstance(ticker, dict):
                current = ticker.get("lastPrice", "0.00")
                return current, current

            return "0.00", "0.00"
        except Exception as e:
            print(f"Error getting price range for {symbol}: {e}")
            return "0.00", "0.00"

    def _extract_causal_factors(
        self, reasoning: str, change_pct: float
    ) -> List[CausalFactor]:
        """Extract causal factors from AI reasoning"""
        factors = []
        reasoning_lower = reasoning.lower()

        # Detect regulatory factors
        if any(word in reasoning_lower for word in ["etf", "sec", "regulation", "regulatory", "approval", "law"]):
            impact = 0.35 if change_pct > 0 else 0.30
            factors.append(CausalFactor(
                factor="Regulatory developments",
                category="REGULATORY",
                impact_score=impact,
                related_news=[],
                explanation=self._extract_sentence(reasoning, ["etf", "sec", "regulation", "regulatory"])
            ))

        # Detect on-chain factors
        if any(word in reasoning_lower for word in ["whale", "accumulation", "wallet", "on-chain", "transfer"]):
            impact = 0.25
            factors.append(CausalFactor(
                factor="On-chain activity",
                category="ON_CHAIN",
                impact_score=impact,
                related_news=[],
                explanation=self._extract_sentence(reasoning, ["whale", "accumulation", "wallet"])
            ))

        # Detect market factors
        if any(word in reasoning_lower for word in ["market", "sentiment", "trading", "volume", "liquidity"]):
            impact = 0.30
            factors.append(CausalFactor(
                factor="Market dynamics",
                category="MARKET",
                impact_score=impact,
                related_news=[],
                explanation=self._extract_sentence(reasoning, ["market", "sentiment", "volume"])
            ))

        # Detect news factors
        if any(word in reasoning_lower for word in ["news", "announcement", "report", "partnership"]):
            impact = 0.20
            factors.append(CausalFactor(
                factor="News and announcements",
                category="NEWS",
                impact_score=impact,
                related_news=[],
                explanation=self._extract_sentence(reasoning, ["news", "announcement"])
            ))

        # Detect technical factors
        if any(word in reasoning_lower for word in ["support", "resistance", "breakout", "technical", "trend"]):
            impact = 0.25
            factors.append(CausalFactor(
                factor="Technical analysis",
                category="TECHNICAL",
                impact_score=impact,
                related_news=[],
                explanation=self._extract_sentence(reasoning, ["support", "resistance", "breakout"])
            ))

        # Default factor if none found
        if not factors:
            direction = "upward" if change_pct > 0 else ("downward" if change_pct < 0 else "sideways")
            factors.append(CausalFactor(
                factor="General market movement",
                category="MARKET",
                impact_score=0.50,
                related_news=[],
                explanation=f"The {direction} price movement appears to be driven by overall market conditions."
            ))

        # Normalize impact scores
        total_impact = sum(f.impact_score for f in factors)
        if total_impact > 0:
            for factor in factors:
                factor.impact_score = round(factor.impact_score / total_impact, 2)

        return factors

    def _extract_sentence(self, text: str, keywords: List[str]) -> str:
        """Extract sentence containing keywords"""
        sentences = text.replace("\n", " ").split(".")
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                return sentence.strip() + "."

        return "Based on AI analysis of market conditions."

    def _generate_summary(
        self, symbol: str, change_str: str, factors: List[CausalFactor]
    ) -> str:
        """Generate summary from causal factors"""
        if not factors:
            return f"{symbol} price change of {change_str} driven by general market conditions."

        # Sort by impact
        sorted_factors = sorted(factors, key=lambda f: f.impact_score, reverse=True)
        main_factor = sorted_factors[0]

        summary = f"{symbol} price change of {change_str} primarily driven by {main_factor.factor.lower()}"

        if len(sorted_factors) > 1:
            secondary = sorted_factors[1]
            summary += f", with additional influence from {secondary.factor.lower()}"

        summary += "."
        return summary
