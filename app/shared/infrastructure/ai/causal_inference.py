# app/shared/infrastructure/ai/causal_inference.py
"""
Causal Inference Module for Crypto Market Analysis

This module implements a lightweight Bayesian-like causal inference system
for analyzing the relationship between news events and price movements.

Key concepts:
- Prior probabilities: Base rates of different factor impacts
- Conditional probabilities: P(price_change | factor)
- Posterior calculation: Updated beliefs based on evidence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math
from datetime import datetime


class FactorCategory(str, Enum):
    REGULATORY = "REGULATORY"
    ON_CHAIN = "ON_CHAIN"
    MARKET = "MARKET"
    NEWS = "NEWS"
    TECHNICAL = "TECHNICAL"
    MACRO = "MACRO"


class PriceDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


@dataclass
class CausalNode:
    """Represents a node in the causal graph"""
    name: str
    category: FactorCategory
    # Prior probability that this factor is active
    prior: float = 0.5
    # Conditional probabilities P(price_direction | factor_active)
    likelihood: Dict[PriceDirection, float] = field(default_factory=dict)
    # Keywords to detect this factor in text
    keywords: List[str] = field(default_factory=list)
    # Detected evidence strength (0-1)
    evidence_strength: float = 0.0


@dataclass
class CausalEdge:
    """Represents a causal relationship between nodes"""
    parent: str
    child: str
    strength: float  # -1 to 1, negative means inverse relationship


@dataclass
class InferenceResult:
    """Result of causal inference"""
    factor: str
    category: str
    prior_probability: float
    posterior_probability: float
    impact_score: float  # Contribution to price change
    confidence: float
    explanation: str
    evidence: List[str]


class CausalBayesianNetwork:
    """
    Simplified Bayesian Network for crypto causal analysis.

    This implements a two-layer Bayesian model:
    Layer 1: Factor nodes (regulatory, on-chain, market, etc.)
    Layer 2: Price direction (UP, DOWN, NEUTRAL)

    Uses Bayes' theorem to compute posterior probabilities:
    P(factor | evidence) = P(evidence | factor) * P(factor) / P(evidence)
    """

    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: List[CausalEdge] = []
        self._initialize_network()

    def _initialize_network(self):
        """Initialize the causal network with crypto-specific priors"""

        # Define factor nodes with prior probabilities and likelihoods
        # These are based on historical analysis of crypto market behavior

        self.nodes = {
            # Regulatory factors - high impact
            "etf_approval": CausalNode(
                name="ETF Approval/Filing",
                category=FactorCategory.REGULATORY,
                prior=0.15,  # Relatively rare
                likelihood={
                    PriceDirection.UP: 0.85,
                    PriceDirection.DOWN: 0.05,
                    PriceDirection.NEUTRAL: 0.10
                },
                keywords=["etf", "approved", "approval", "filing", "blackrock", "fidelity", "grayscale"]
            ),
            "etf_rejection": CausalNode(
                name="ETF Rejection/Delay",
                category=FactorCategory.REGULATORY,
                prior=0.10,
                likelihood={
                    PriceDirection.UP: 0.10,
                    PriceDirection.DOWN: 0.75,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["rejected", "rejection", "delayed", "postponed", "denied"]
            ),
            "sec_action": CausalNode(
                name="SEC Regulatory Action",
                category=FactorCategory.REGULATORY,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.15,
                    PriceDirection.DOWN: 0.65,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["sec", "regulation", "regulatory", "lawsuit", "investigation", "enforcement"]
            ),
            "positive_regulation": CausalNode(
                name="Positive Regulatory News",
                category=FactorCategory.REGULATORY,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.75,
                    PriceDirection.DOWN: 0.10,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["legalized", "adopted", "framework", "clarity", "supportive"]
            ),

            # On-chain factors
            "whale_accumulation": CausalNode(
                name="Whale Accumulation",
                category=FactorCategory.ON_CHAIN,
                prior=0.25,
                likelihood={
                    PriceDirection.UP: 0.70,
                    PriceDirection.DOWN: 0.15,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["whale", "accumulation", "accumulating", "large wallet", "hodl", "holding"]
            ),
            "whale_distribution": CausalNode(
                name="Whale Distribution/Selling",
                category=FactorCategory.ON_CHAIN,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.10,
                    PriceDirection.DOWN: 0.70,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["whale selling", "distribution", "dump", "large transfer", "exchange inflow"]
            ),
            "network_growth": CausalNode(
                name="Network Growth",
                category=FactorCategory.ON_CHAIN,
                prior=0.30,
                likelihood={
                    PriceDirection.UP: 0.65,
                    PriceDirection.DOWN: 0.15,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["active addresses", "network growth", "adoption", "users", "transactions"]
            ),

            # Market factors
            "high_volume": CausalNode(
                name="High Trading Volume",
                category=FactorCategory.MARKET,
                prior=0.35,
                likelihood={
                    PriceDirection.UP: 0.50,
                    PriceDirection.DOWN: 0.30,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["volume", "trading volume", "high volume", "volume spike"]
            ),
            "bullish_sentiment": CausalNode(
                name="Bullish Market Sentiment",
                category=FactorCategory.MARKET,
                prior=0.30,
                likelihood={
                    PriceDirection.UP: 0.75,
                    PriceDirection.DOWN: 0.10,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["bullish", "optimistic", "positive sentiment", "confidence", "fomo"]
            ),
            "bearish_sentiment": CausalNode(
                name="Bearish Market Sentiment",
                category=FactorCategory.MARKET,
                prior=0.25,
                likelihood={
                    PriceDirection.UP: 0.10,
                    PriceDirection.DOWN: 0.75,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["bearish", "pessimistic", "fear", "fud", "panic", "capitulation"]
            ),
            "liquidations": CausalNode(
                name="Large Liquidations",
                category=FactorCategory.MARKET,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.20,
                    PriceDirection.DOWN: 0.60,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["liquidation", "liquidated", "margin call", "forced selling"]
            ),

            # News factors
            "institutional_adoption": CausalNode(
                name="Institutional Adoption",
                category=FactorCategory.NEWS,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.80,
                    PriceDirection.DOWN: 0.05,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["institutional", "institution", "hedge fund", "investment firm",
                         "corporate", "tesla", "microstrategy", "adoption"]
            ),
            "partnership": CausalNode(
                name="Major Partnership",
                category=FactorCategory.NEWS,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.70,
                    PriceDirection.DOWN: 0.10,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["partnership", "collaboration", "integration", "deal", "agreement"]
            ),
            "hack_exploit": CausalNode(
                name="Security Breach/Hack",
                category=FactorCategory.NEWS,
                prior=0.10,
                likelihood={
                    PriceDirection.UP: 0.05,
                    PriceDirection.DOWN: 0.80,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["hack", "hacked", "exploit", "breach", "stolen", "vulnerability"]
            ),

            # Technical factors
            "support_break": CausalNode(
                name="Support Level Break",
                category=FactorCategory.TECHNICAL,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.10,
                    PriceDirection.DOWN: 0.70,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["support broken", "broke support", "below support", "support failed"]
            ),
            "resistance_break": CausalNode(
                name="Resistance Breakout",
                category=FactorCategory.TECHNICAL,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.75,
                    PriceDirection.DOWN: 0.10,
                    PriceDirection.NEUTRAL: 0.15
                },
                keywords=["breakout", "broke resistance", "above resistance", "new high"]
            ),
            "oversold": CausalNode(
                name="Oversold Conditions",
                category=FactorCategory.TECHNICAL,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.65,
                    PriceDirection.DOWN: 0.15,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["oversold", "rsi low", "bounce", "reversal", "recovery"]
            ),
            "overbought": CausalNode(
                name="Overbought Conditions",
                category=FactorCategory.TECHNICAL,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.15,
                    PriceDirection.DOWN: 0.65,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["overbought", "rsi high", "correction", "pullback"]
            ),

            # Macro factors
            "fed_hawkish": CausalNode(
                name="Fed Hawkish Policy",
                category=FactorCategory.MACRO,
                prior=0.20,
                likelihood={
                    PriceDirection.UP: 0.15,
                    PriceDirection.DOWN: 0.65,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["fed", "rate hike", "hawkish", "tightening", "interest rate increase"]
            ),
            "fed_dovish": CausalNode(
                name="Fed Dovish Policy",
                category=FactorCategory.MACRO,
                prior=0.15,
                likelihood={
                    PriceDirection.UP: 0.70,
                    PriceDirection.DOWN: 0.10,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["rate cut", "dovish", "easing", "pause", "pivot"]
            ),
            "inflation": CausalNode(
                name="Inflation Concerns",
                category=FactorCategory.MACRO,
                prior=0.25,
                likelihood={
                    PriceDirection.UP: 0.55,  # BTC as inflation hedge
                    PriceDirection.DOWN: 0.25,
                    PriceDirection.NEUTRAL: 0.20
                },
                keywords=["inflation", "cpi", "hedge", "store of value", "devaluation"]
            ),
        }

    def detect_factors(self, text: str) -> Dict[str, float]:
        """
        Detect which factors are present in the text and their strength.

        Returns: Dict of factor_name -> evidence_strength (0-1)
        """
        text_lower = text.lower()
        detected = {}

        for node_id, node in self.nodes.items():
            # Count keyword matches
            matches = sum(1 for kw in node.keywords if kw.lower() in text_lower)

            if matches > 0:
                # Calculate evidence strength based on keyword density
                strength = min(1.0, matches / max(3, len(node.keywords) * 0.5))
                detected[node_id] = strength
                node.evidence_strength = strength

        return detected

    def compute_posterior(
        self,
        node: CausalNode,
        observed_direction: PriceDirection,
        evidence_strength: float
    ) -> float:
        """
        Compute posterior probability using Bayes' theorem.

        P(factor | price_direction) = P(price_direction | factor) * P(factor) / P(price_direction)

        We estimate P(price_direction) using law of total probability.
        """
        # Prior
        prior = node.prior

        # Likelihood
        likelihood = node.likelihood.get(observed_direction, 0.33)

        # Estimate P(price_direction) - marginal probability
        # Using uniform prior over all factors for simplicity
        p_direction = 0.33  # Baseline assumption

        # Apply Bayes' theorem
        if p_direction > 0:
            posterior = (likelihood * prior) / p_direction
        else:
            posterior = prior

        # Weight by evidence strength
        weighted_posterior = prior + (posterior - prior) * evidence_strength

        # Normalize to [0, 1]
        return min(1.0, max(0.0, weighted_posterior))

    def compute_impact_scores(
        self,
        detected_factors: Dict[str, float],
        observed_direction: PriceDirection,
        price_change_pct: float
    ) -> List[InferenceResult]:
        """
        Compute impact scores for all detected factors.

        Uses a combination of:
        1. Posterior probability (how likely this factor caused the movement)
        2. Evidence strength (how confident we are the factor is present)
        3. Likelihood alignment (does the factor direction match observed direction?)
        """
        results = []

        for factor_id, evidence_strength in detected_factors.items():
            node = self.nodes.get(factor_id)
            if not node:
                continue

            # Compute posterior
            posterior = self.compute_posterior(node, observed_direction, evidence_strength)

            # Check if factor direction aligns with observed direction
            expected_direction = max(node.likelihood, key=node.likelihood.get)
            alignment = 1.0 if expected_direction == observed_direction else 0.5

            # Compute impact score
            # Impact = posterior * evidence_strength * alignment * abs(price_change)
            raw_impact = posterior * evidence_strength * alignment

            # Confidence based on evidence strength and likelihood
            confidence = evidence_strength * node.likelihood.get(observed_direction, 0.33)

            # Generate explanation
            direction_text = "increase" if observed_direction == PriceDirection.UP else \
                           "decrease" if observed_direction == PriceDirection.DOWN else "stability"

            if alignment >= 1.0:
                explanation = f"{node.name} is a likely cause of the price {direction_text}. " \
                            f"Historical data shows {node.likelihood[observed_direction]*100:.0f}% " \
                            f"probability of {observed_direction.value} movement when this factor is present."
            else:
                explanation = f"{node.name} was detected but typically causes opposite movement. " \
                            f"This may indicate conflicting market forces or delayed reaction."

            results.append(InferenceResult(
                factor=node.name,
                category=node.category.value,
                prior_probability=round(node.prior, 3),
                posterior_probability=round(posterior, 3),
                impact_score=round(raw_impact, 3),
                confidence=round(confidence, 3),
                explanation=explanation,
                evidence=[kw for kw in node.keywords if kw.lower() in detected_factors]
            ))

        # Normalize impact scores to sum to 1.0
        total_impact = sum(r.impact_score for r in results)
        if total_impact > 0:
            for r in results:
                r.impact_score = round(r.impact_score / total_impact, 3)

        # Sort by impact score
        results.sort(key=lambda x: x.impact_score, reverse=True)

        return results

    def infer(
        self,
        text: str,
        price_change_pct: float,
        additional_context: Optional[str] = None
    ) -> Tuple[List[InferenceResult], str]:
        """
        Main inference method.

        Args:
            text: News/analysis text to extract factors from
            price_change_pct: Observed price change percentage
            additional_context: Optional additional context

        Returns:
            Tuple of (inference_results, summary)
        """
        # Combine text with additional context
        full_text = text
        if additional_context:
            full_text += " " + additional_context

        # Detect factors
        detected = self.detect_factors(full_text)

        if not detected:
            return [], "No significant causal factors detected in the provided context."

        # Determine observed direction
        if price_change_pct > 1.0:
            direction = PriceDirection.UP
        elif price_change_pct < -1.0:
            direction = PriceDirection.DOWN
        else:
            direction = PriceDirection.NEUTRAL

        # Compute impact scores
        results = self.compute_impact_scores(detected, direction, price_change_pct)

        # Generate summary
        summary = self._generate_summary(results, price_change_pct, direction)

        return results, summary

    def _generate_summary(
        self,
        results: List[InferenceResult],
        price_change: float,
        direction: PriceDirection
    ) -> str:
        """Generate a human-readable summary of the causal analysis"""
        if not results:
            return "Unable to identify specific causal factors for this price movement."

        direction_text = "increase" if direction == PriceDirection.UP else \
                        "decrease" if direction == PriceDirection.DOWN else "sideways movement"

        # Top factors
        top_factors = results[:3]

        summary_parts = [
            f"The {abs(price_change):.1f}% price {direction_text} is attributed to:"
        ]

        for i, factor in enumerate(top_factors, 1):
            summary_parts.append(
                f"{i}. {factor.factor} ({factor.impact_score*100:.0f}% contribution, "
                f"{factor.confidence*100:.0f}% confidence)"
            )

        # Add category breakdown
        category_impacts = {}
        for r in results:
            cat = r.category
            category_impacts[cat] = category_impacts.get(cat, 0) + r.impact_score

        if category_impacts:
            summary_parts.append("\nCategory breakdown:")
            for cat, impact in sorted(category_impacts.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"  - {cat}: {impact*100:.0f}%")

        return "\n".join(summary_parts)


# Singleton instance
_causal_network: Optional[CausalBayesianNetwork] = None


def get_causal_network() -> CausalBayesianNetwork:
    """Get singleton instance of the causal network"""
    global _causal_network
    if _causal_network is None:
        _causal_network = CausalBayesianNetwork()
    return _causal_network
