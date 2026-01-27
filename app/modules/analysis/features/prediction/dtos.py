from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TargetPrice(BaseModel):
    low: str
    mid: str
    high: str


class PredictionData(BaseModel):
    direction: str  # UP, DOWN, NEUTRAL
    confidence: float = Field(..., ge=0.0, le=1.0)
    target_price: TargetPrice
    support_levels: List[str]
    resistance_levels: List[str]


class SymbolPredictionResponse(BaseModel):
    symbol: str
    timeframe: str
    current_price: str
    prediction: PredictionData
    model_version: str
    generated_at: datetime


class MultiPredictionItem(BaseModel):
    symbol: str
    direction: str
    confidence: float
    target_mid: str
    current_price: str


class MultiPredictionResponse(BaseModel):
    timeframe: str
    predictions: List[MultiPredictionItem]
    model_version: str
    generated_at: datetime
