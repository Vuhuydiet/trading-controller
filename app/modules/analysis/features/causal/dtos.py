from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class FeatureAttribution(BaseModel):
    """SHAP-like feature attribution"""
    feature: str
    category: str
    shap_value: float  # Contribution to prediction (-1 to 1)
    direction: str  # "positive" or "negative"
    importance_rank: int
    explanation: str


class ExplainabilityData(BaseModel):
    """Complete explainability data for a prediction"""
    prediction: str  # BULLISH, BEARISH, NEUTRAL
    prediction_confidence: float
    base_value: float
    total_positive_contribution: float
    total_negative_contribution: float
    feature_attributions: List[FeatureAttribution]
    visualization_data: Optional[Dict[str, Any]] = None


class CausalFactor(BaseModel):
    """Causal factor with Bayesian probabilities"""
    factor: str
    category: str  # REGULATORY, ON_CHAIN, MARKET, NEWS, TECHNICAL, MACRO
    impact_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    prior_probability: float = Field(default=0.2, ge=0.0, le=1.0)
    posterior_probability: float = Field(default=0.4, ge=0.0, le=1.0)
    related_news: List[str] = Field(default_factory=list)
    explanation: str


class PriceChange(BaseModel):
    price_from: str = Field(..., alias="from")
    price_to: str = Field(..., alias="to")
    percent: str

    class Config:
        populate_by_name = True


class Period(BaseModel):
    period_from: datetime = Field(..., alias="from")
    period_to: datetime = Field(..., alias="to")

    class Config:
        populate_by_name = True


class CausalAnalysisResponse(BaseModel):
    """Response with full causal analysis and explainability"""
    symbol: str
    period: Period
    price_change: PriceChange
    causal_factors: List[CausalFactor]
    summary: str
    explainability: Optional[ExplainabilityData] = None
    generated_at: datetime


class ExplainPriceRequest(BaseModel):
    symbol: str
    price_from: str
    price_to: str
    period_from: datetime
    period_to: datetime
    additional_context: Optional[str] = None


class ExplainPriceResponse(BaseModel):
    """Response with full price movement explanation"""
    symbol: str
    price_change: PriceChange
    causal_factors: List[CausalFactor]
    summary: str
    confidence: float
    explainability: Optional[ExplainabilityData] = None
    generated_at: datetime
