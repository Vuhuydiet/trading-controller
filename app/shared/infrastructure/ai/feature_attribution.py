# app/shared/infrastructure/ai/feature_attribution.py
"""
Feature Attribution Module (SHAP-like Explainability)

This module provides SHAP-inspired feature attribution for crypto market predictions.
Instead of using actual SHAP values (which require a trained ML model), we implement
a similar concept using our Bayesian causal network to compute feature contributions.

Key concepts:
- Base value: Expected prediction without any features
- SHAP values: Contribution of each feature to the prediction
- Feature importance: Ranking of features by contribution magnitude
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class PredictionType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class FeatureContribution:
    """Represents the contribution of a single feature to the prediction"""
    feature_name: str
    category: str
    raw_value: float  # The actual value/strength detected (0-1)
    shap_value: float  # Contribution to prediction (-1 to 1)
    direction: str  # "positive" or "negative" contribution
    importance_rank: int = 0
    explanation: str = ""


@dataclass
class AttributionResult:
    """Complete attribution result for a prediction"""
    prediction: PredictionType
    confidence: float
    base_value: float  # Expected value without features
    features: List[FeatureContribution]
    total_positive_contribution: float
    total_negative_contribution: float
    summary: str


class FeatureAttributor:
    """
    Computes SHAP-like feature attributions for market predictions.

    This implementation uses a simplified additive feature attribution:
    prediction = base_value + sum(shap_values)

    Where each shap_value represents how much a feature pushes the
    prediction away from the base value.
    """

    def __init__(self):
        # Base value represents the expected prediction without any features
        # For a 3-class problem (bullish/bearish/neutral), base = 0 (neutral)
        self.base_value = 0.0

        # Feature weights learned from domain knowledge
        # These represent how much each feature type typically affects predictions
        self.feature_weights = {
            # Regulatory features - high impact
            "REGULATORY": {
                "positive": ["etf_approval", "positive_regulation", "adoption"],
                "negative": ["etf_rejection", "sec_action", "ban", "lawsuit"],
                "base_weight": 0.35
            },
            # On-chain features
            "ON_CHAIN": {
                "positive": ["accumulation", "hodl", "network_growth", "hash_rate"],
                "negative": ["distribution", "selling", "exchange_inflow"],
                "base_weight": 0.25
            },
            # Market features
            "MARKET": {
                "positive": ["bullish", "volume_up", "buy_pressure", "fomo"],
                "negative": ["bearish", "liquidation", "sell_pressure", "fear"],
                "base_weight": 0.30
            },
            # News features
            "NEWS": {
                "positive": ["partnership", "institutional", "adoption", "upgrade"],
                "negative": ["hack", "exploit", "scam", "bankruptcy"],
                "base_weight": 0.20
            },
            # Technical features
            "TECHNICAL": {
                "positive": ["breakout", "support_hold", "oversold", "golden_cross"],
                "negative": ["breakdown", "resistance_reject", "overbought", "death_cross"],
                "base_weight": 0.25
            },
            # Macro features
            "MACRO": {
                "positive": ["dovish", "rate_cut", "stimulus", "risk_on"],
                "negative": ["hawkish", "rate_hike", "tightening", "risk_off"],
                "base_weight": 0.20
            }
        }

    def compute_attribution(
        self,
        detected_features: Dict[str, Dict],
        prediction_score: float,  # -1 (bearish) to 1 (bullish)
        price_change_pct: float
    ) -> AttributionResult:
        """
        Compute feature attributions for a prediction.

        Args:
            detected_features: Dict of feature_name -> {category, strength, direction}
            prediction_score: The model's prediction score (-1 to 1)
            price_change_pct: Actual price change for validation

        Returns:
            AttributionResult with SHAP-like attributions
        """
        contributions = []

        # Calculate raw contributions for each feature
        for feature_name, feature_info in detected_features.items():
            category = feature_info.get("category", "MARKET")
            strength = feature_info.get("strength", 0.5)
            is_positive = feature_info.get("is_positive", True)

            # Get category weight
            category_config = self.feature_weights.get(category, {"base_weight": 0.20})
            base_weight = category_config["base_weight"]

            # Calculate SHAP value
            # SHAP value = weight * strength * direction
            direction_multiplier = 1.0 if is_positive else -1.0
            shap_value = base_weight * strength * direction_multiplier

            contributions.append(FeatureContribution(
                feature_name=feature_name,
                category=category,
                raw_value=strength,
                shap_value=shap_value,
                direction="positive" if shap_value > 0 else "negative",
                explanation=self._generate_feature_explanation(
                    feature_name, category, strength, is_positive
                )
            ))

        # Normalize SHAP values to match prediction
        total_contribution = sum(c.shap_value for c in contributions)
        if total_contribution != 0 and len(contributions) > 0:
            # Scale contributions to match the prediction score
            scale_factor = prediction_score / total_contribution if total_contribution != 0 else 1
            for c in contributions:
                c.shap_value = round(c.shap_value * scale_factor, 4)

        # Sort by absolute contribution and assign ranks
        contributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
        for i, c in enumerate(contributions):
            c.importance_rank = i + 1

        # Calculate totals
        total_positive = sum(c.shap_value for c in contributions if c.shap_value > 0)
        total_negative = sum(c.shap_value for c in contributions if c.shap_value < 0)

        # Determine prediction type
        if prediction_score > 0.2:
            prediction = PredictionType.BULLISH
        elif prediction_score < -0.2:
            prediction = PredictionType.BEARISH
        else:
            prediction = PredictionType.NEUTRAL

        # Calculate confidence
        confidence = min(1.0, abs(prediction_score) + 0.3)

        # Generate summary
        summary = self._generate_summary(contributions, prediction, price_change_pct)

        return AttributionResult(
            prediction=prediction,
            confidence=round(confidence, 3),
            base_value=self.base_value,
            features=contributions,
            total_positive_contribution=round(total_positive, 4),
            total_negative_contribution=round(total_negative, 4),
            summary=summary
        )

    def _generate_feature_explanation(
        self,
        feature_name: str,
        category: str,
        strength: float,
        is_positive: bool
    ) -> str:
        """Generate explanation for a feature's contribution"""
        direction = "bullish" if is_positive else "bearish"
        strength_desc = "strongly" if strength > 0.7 else "moderately" if strength > 0.4 else "slightly"

        return f"{feature_name} ({category}) {strength_desc} pushes prediction toward {direction} " \
               f"with {strength*100:.0f}% confidence."

    def _generate_summary(
        self,
        contributions: List[FeatureContribution],
        prediction: PredictionType,
        price_change: float
    ) -> str:
        """Generate SHAP-style summary"""
        if not contributions:
            return "No significant features detected for attribution."

        lines = [
            f"Prediction: {prediction.value}",
            f"Base value: {self.base_value:.2f} (neutral expectation)",
            "",
            "Feature Contributions (SHAP values):",
            "=" * 50
        ]

        # Add feature bars
        max_width = 30
        for c in contributions[:5]:  # Top 5 features
            bar_width = int(abs(c.shap_value) * max_width * 2)
            if c.shap_value > 0:
                bar = " " * max_width + "│" + "█" * bar_width
            else:
                bar = " " * (max_width - bar_width) + "█" * bar_width + "│"

            lines.append(f"{c.feature_name[:20]:<20} {bar} {c.shap_value:+.3f}")

        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Total positive contribution: +{sum(c.shap_value for c in contributions if c.shap_value > 0):.3f}")
        lines.append(f"Total negative contribution: {sum(c.shap_value for c in contributions if c.shap_value < 0):.3f}")

        return "\n".join(lines)

    def format_for_api(
        self,
        result: AttributionResult
    ) -> Dict:
        """Format attribution result for API response"""
        return {
            "prediction": result.prediction.value,
            "confidence": result.confidence,
            "base_value": result.base_value,
            "contributions": {
                "positive": result.total_positive_contribution,
                "negative": result.total_negative_contribution,
                "net": round(result.total_positive_contribution + result.total_negative_contribution, 4)
            },
            "features": [
                {
                    "rank": f.importance_rank,
                    "feature": f.feature_name,
                    "category": f.category,
                    "shap_value": f.shap_value,
                    "direction": f.direction,
                    "raw_strength": f.raw_value,
                    "explanation": f.explanation
                }
                for f in result.features
            ],
            "visualization": self._generate_waterfall_data(result)
        }

    def _generate_waterfall_data(self, result: AttributionResult) -> Dict:
        """Generate data for waterfall chart visualization"""
        waterfall = {
            "base": result.base_value,
            "steps": [],
            "final": result.base_value + result.total_positive_contribution + result.total_negative_contribution
        }

        cumulative = result.base_value
        for f in result.features[:10]:  # Top 10 for visualization
            waterfall["steps"].append({
                "feature": f.feature_name,
                "value": f.shap_value,
                "cumulative": cumulative + f.shap_value
            })
            cumulative += f.shap_value

        return waterfall


class ExplainabilityEngine:
    """
    High-level explainability engine that combines causal inference
    with feature attribution.
    """

    def __init__(self):
        self.causal_network = None  # Lazy load to avoid circular import
        self.attributor = FeatureAttributor()

    def _get_causal_network(self):
        """Lazy load causal network to avoid circular imports"""
        if self.causal_network is None:
            from app.shared.infrastructure.ai.causal_inference import get_causal_network
            self.causal_network = get_causal_network()
        return self.causal_network

    def explain_prediction(
        self,
        text: str,
        price_change_pct: float,
        prediction_score: Optional[float] = None
    ) -> Dict:
        """
        Generate comprehensive explanation for a market prediction.

        Args:
            text: News/analysis text
            price_change_pct: Observed or predicted price change
            prediction_score: Optional model prediction score

        Returns:
            Dict with causal analysis and feature attribution
        """
        # Run causal inference
        causal_results, causal_summary = self._get_causal_network().infer(text, price_change_pct)

        # Convert causal results to feature format
        detected_features = {}
        for cr in causal_results:
            detected_features[cr.factor] = {
                "category": cr.category,
                "strength": cr.confidence,
                "is_positive": cr.impact_score > 0 and price_change_pct > 0
            }

        # Compute prediction score if not provided
        if prediction_score is None:
            # Use causal results to estimate
            if price_change_pct > 2:
                prediction_score = min(1.0, price_change_pct / 10)
            elif price_change_pct < -2:
                prediction_score = max(-1.0, price_change_pct / 10)
            else:
                prediction_score = price_change_pct / 5

        # Run feature attribution
        attribution = self.attributor.compute_attribution(
            detected_features,
            prediction_score,
            price_change_pct
        )

        return {
            "causal_analysis": {
                "factors": [
                    {
                        "factor": cr.factor,
                        "category": cr.category,
                        "impact_score": cr.impact_score,
                        "confidence": cr.confidence,
                        "prior": cr.prior_probability,
                        "posterior": cr.posterior_probability,
                        "explanation": cr.explanation
                    }
                    for cr in causal_results
                ],
                "summary": causal_summary
            },
            "feature_attribution": self.attributor.format_for_api(attribution),
            "combined_explanation": self._generate_combined_explanation(
                causal_results, attribution, price_change_pct
            )
        }

    def _generate_combined_explanation(
        self,
        causal_results,
        attribution: AttributionResult,
        price_change: float
    ) -> str:
        """Generate user-friendly combined explanation"""
        direction = "increased" if price_change > 0 else "decreased" if price_change < 0 else "remained stable"

        lines = [
            f"📊 MARKET ANALYSIS EXPLANATION",
            f"",
            f"The price {direction} by {abs(price_change):.2f}%",
            f"",
            f"🔍 CAUSAL FACTORS IDENTIFIED:"
        ]

        for i, cr in enumerate(causal_results[:3], 1):
            emoji = "🟢" if cr.impact_score > 0.2 else "🔴" if cr.impact_score < -0.1 else "🟡"
            lines.append(f"   {emoji} {i}. {cr.factor}")
            lines.append(f"      Impact: {cr.impact_score*100:.0f}% | Confidence: {cr.confidence*100:.0f}%")

        lines.extend([
            "",
            f"📈 PREDICTION BREAKDOWN:",
            f"   Prediction: {attribution.prediction.value}",
            f"   Confidence: {attribution.confidence*100:.0f}%",
            "",
            f"⚖️ CONTRIBUTION BALANCE:",
            f"   Bullish factors: +{attribution.total_positive_contribution:.2f}",
            f"   Bearish factors: {attribution.total_negative_contribution:.2f}",
        ])

        return "\n".join(lines)


# Singleton instance
_explainability_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    """Get singleton instance of the explainability engine"""
    global _explainability_engine
    if _explainability_engine is None:
        _explainability_engine = ExplainabilityEngine()
    return _explainability_engine
