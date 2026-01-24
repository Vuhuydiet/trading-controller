from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CausalFactor(BaseModel):
    factor: str
    category: str  # REGULATORY, ON_CHAIN, MARKET, NEWS, TECHNICAL
    impact_score: float = Field(..., ge=0.0, le=1.0)
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
    symbol: str
    period: Period
    price_change: PriceChange
    causal_factors: List[CausalFactor]
    summary: str
    generated_at: datetime


class ExplainPriceRequest(BaseModel):
    symbol: str
    price_from: str
    price_to: str
    period_from: datetime
    period_to: datetime
    additional_context: Optional[str] = None


class ExplainPriceResponse(BaseModel):
    symbol: str
    price_change: PriceChange
    causal_factors: List[CausalFactor]
    summary: str
    confidence: float
    generated_at: datetime
