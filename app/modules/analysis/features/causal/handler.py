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
    FeatureAttribution,
    ExplainabilityData,
)
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort
from app.modules.analysis.domain.entities import CausalAnalysis
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient
from app.shared.infrastructure.ai.causal_inference import get_causal_network, PriceDirection
from app.shared.infrastructure.ai.feature_attribution import get_explainability_engine
from app.shared.core.logging_config import get_logger

logger = get_logger(__name__)


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
        self.causal_network = get_causal_network()
        self.explainability_engine = get_explainability_engine()

    async def get_causal_analysis(
        self,
        symbol: str,
        period_from: Optional[datetime] = None,
        period_to: Optional[datetime] = None,
    ) -> CausalAnalysisResponse:
        """Get causal reasoning for price movement with Bayesian inference"""

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
        Consider: regulatory news, on-chain data, market sentiment, technical factors, macro economics.
        """

        # Get AI reasoning
        reasoning_result = await self.reasoner.explain_market_trend(
            news=context,
            price_change=change_pct
        )

        # Use Bayesian Causal Network for inference
        causal_results, causal_summary = self.causal_network.infer(
            text=reasoning_result.reasoning,
            price_change_pct=change_pct,
            additional_context=context
        )

        # Convert to CausalFactor DTOs with Bayesian posteriors
        factors = []
        for cr in causal_results:
            factors.append(CausalFactor(
                factor=cr.factor,
                category=cr.category,
                impact_score=cr.impact_score,
                confidence=cr.confidence,
                prior_probability=cr.prior_probability,
                posterior_probability=cr.posterior_probability,
                related_news=[],
                explanation=cr.explanation
            ))

        # If no factors from Bayesian network, fall back to keyword extraction
        if not factors:
            factors = self._extract_causal_factors_fallback(reasoning_result.reasoning, change_pct)

        # Generate explainability data
        explainability = await self._generate_explainability(
            reasoning_result.reasoning,
            change_pct,
            factors
        )

        # Generate enhanced summary
        summary = self._generate_enhanced_summary(symbol, change_str, factors, causal_summary)

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
            explainability=explainability,
            generated_at=datetime.now(timezone.utc),
        )

    async def explain_price_movement(
        self, request: ExplainPriceRequest
    ) -> ExplainPriceResponse:
        """Explain a specific price movement with full explainability"""

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

        # Use full explainability engine
        full_explanation = self.explainability_engine.explain_prediction(
            text=reasoning_result.reasoning + " " + (request.additional_context or ""),
            price_change_pct=change_pct
        )

        # Extract factors from causal analysis
        factors = []
        for cf in full_explanation["causal_analysis"]["factors"]:
            factors.append(CausalFactor(
                factor=cf["factor"],
                category=cf["category"],
                impact_score=cf["impact_score"],
                confidence=cf["confidence"],
                prior_probability=cf["prior"],
                posterior_probability=cf["posterior"],
                related_news=[],
                explanation=cf["explanation"]
            ))

        # Create explainability data
        attr_data = full_explanation["feature_attribution"]
        explainability = ExplainabilityData(
            prediction=attr_data["prediction"],
            prediction_confidence=attr_data["confidence"],
            base_value=attr_data["base_value"],
            total_positive_contribution=attr_data["contributions"]["positive"],
            total_negative_contribution=attr_data["contributions"]["negative"],
            feature_attributions=[
                FeatureAttribution(
                    feature=f["feature"],
                    category=f["category"],
                    shap_value=f["shap_value"],
                    direction=f["direction"],
                    importance_rank=f["rank"],
                    explanation=f["explanation"]
                )
                for f in attr_data["features"]
            ],
            visualization_data=attr_data["visualization"]
        )

        # Generate summary
        summary = full_explanation["combined_explanation"]

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
            explainability=explainability,
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
            logger.error(f"Error getting price range for {symbol}: {e}")
            return "0.00", "0.00"

    async def _generate_explainability(
        self,
        reasoning: str,
        change_pct: float,
        factors: List[CausalFactor]
    ) -> Optional[ExplainabilityData]:
        """Generate explainability data from factors"""
        try:
            # Convert factors to feature format
            detected_features = {}
            for f in factors:
                detected_features[f.factor] = {
                    "category": f.category,
                    "strength": f.confidence,
                    "is_positive": f.impact_score > 0
                }

            # Get attribution
            from app.shared.infrastructure.ai.feature_attribution import FeatureAttributor
            attributor = FeatureAttributor()

            # Calculate prediction score from change
            if change_pct > 2:
                prediction_score = min(1.0, change_pct / 10)
            elif change_pct < -2:
                prediction_score = max(-1.0, change_pct / 10)
            else:
                prediction_score = change_pct / 5

            result = attributor.compute_attribution(
                detected_features,
                prediction_score,
                change_pct
            )

            return ExplainabilityData(
                prediction=result.prediction.value,
                prediction_confidence=result.confidence,
                base_value=result.base_value,
                total_positive_contribution=result.total_positive_contribution,
                total_negative_contribution=result.total_negative_contribution,
                feature_attributions=[
                    FeatureAttribution(
                        feature=f.feature_name,
                        category=f.category,
                        shap_value=f.shap_value,
                        direction=f.direction,
                        importance_rank=f.importance_rank,
                        explanation=f.explanation
                    )
                    for f in result.features
                ],
                visualization_data=attributor._generate_waterfall_data(result)
            )
        except Exception as e:
            logger.error(f"Error generating explainability: {e}")
            return None

    def _extract_causal_factors_fallback(
        self, reasoning: str, change_pct: float
    ) -> List[CausalFactor]:
        """Fallback keyword-based extraction when Bayesian network finds nothing"""
        factors = []
        reasoning_lower = reasoning.lower()

        factor_configs = [
            {
                "keywords": ["etf", "sec", "regulation", "regulatory", "approval", "law"],
                "factor": "Regulatory developments",
                "category": "REGULATORY",
                "base_impact": 0.35
            },
            {
                "keywords": ["whale", "accumulation", "wallet", "on-chain", "transfer"],
                "factor": "On-chain activity",
                "category": "ON_CHAIN",
                "base_impact": 0.25
            },
            {
                "keywords": ["market", "sentiment", "trading", "volume", "liquidity"],
                "factor": "Market dynamics",
                "category": "MARKET",
                "base_impact": 0.30
            },
            {
                "keywords": ["news", "announcement", "report", "partnership"],
                "factor": "News and announcements",
                "category": "NEWS",
                "base_impact": 0.20
            },
            {
                "keywords": ["support", "resistance", "breakout", "technical", "trend"],
                "factor": "Technical analysis",
                "category": "TECHNICAL",
                "base_impact": 0.25
            },
            {
                "keywords": ["fed", "interest", "inflation", "macro", "economy"],
                "factor": "Macroeconomic factors",
                "category": "MACRO",
                "base_impact": 0.20
            }
        ]

        for config in factor_configs:
            if any(word in reasoning_lower for word in config["keywords"]):
                impact = config["base_impact"] if change_pct > 0 else config["base_impact"] * 0.9
                factors.append(CausalFactor(
                    factor=config["factor"],
                    category=config["category"],
                    impact_score=impact,
                    confidence=0.5,  # Lower confidence for keyword-based
                    prior_probability=0.2,
                    posterior_probability=0.4,
                    related_news=[],
                    explanation=self._extract_sentence(reasoning, config["keywords"])
                ))

        # Default factor if none found
        if not factors:
            direction = "upward" if change_pct > 0 else ("downward" if change_pct < 0 else "sideways")
            factors.append(CausalFactor(
                factor="General market movement",
                category="MARKET",
                impact_score=0.50,
                confidence=0.3,
                prior_probability=0.33,
                posterior_probability=0.33,
                related_news=[],
                explanation=f"The {direction} price movement appears to be driven by overall market conditions."
            ))

        # Normalize impact scores
        total_impact = sum(f.impact_score for f in factors)
        if total_impact > 0:
            for factor in factors:
                factor.impact_score = round(factor.impact_score / total_impact, 3)

        return factors

    def _extract_sentence(self, text: str, keywords: List[str]) -> str:
        """Extract sentence containing keywords"""
        sentences = text.replace("\n", " ").split(".")
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                return sentence.strip() + "."

        return "Based on AI analysis of market conditions."

    def _generate_enhanced_summary(
        self,
        symbol: str,
        change_str: str,
        factors: List[CausalFactor],
        causal_summary: str
    ) -> str:
        """Generate enhanced summary combining all analyses"""
        if not factors:
            return f"{symbol} price change of {change_str} driven by general market conditions."

        # Sort by impact
        sorted_factors = sorted(factors, key=lambda f: f.impact_score, reverse=True)
        main_factor = sorted_factors[0]

        lines = [
            f"📊 {symbol} Analysis Summary",
            f"",
            f"Price Change: {change_str}",
            f"",
            f"🔍 Primary Driver: {main_factor.factor}",
            f"   - Impact: {main_factor.impact_score*100:.0f}%",
            f"   - Confidence: {main_factor.confidence*100:.0f}%",
            f"   - Bayesian Posterior: {main_factor.posterior_probability:.2f}",
        ]

        if len(sorted_factors) > 1:
            lines.append(f"")
            lines.append(f"📈 Secondary Factors:")
            for f in sorted_factors[1:3]:
                lines.append(f"   - {f.factor}: {f.impact_score*100:.0f}% impact")

        lines.append(f"")
        lines.append(f"💡 {causal_summary}")

        return "\n".join(lines)
