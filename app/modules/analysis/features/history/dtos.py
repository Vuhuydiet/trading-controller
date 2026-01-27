from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PredictionRecord(BaseModel):
    id: int
    predicted_direction: str
    predicted_at: datetime
    target_price: str
    actual_price: Optional[str] = None
    actual_direction: Optional[str] = None
    is_correct: Optional[bool] = None
    verified_at: Optional[datetime] = None


class AccuracyStats(BaseModel):
    total_predictions: int
    verified_predictions: int
    correct_predictions: int
    accuracy_rate: float = Field(..., ge=0.0, le=1.0)
    up_predictions: int
    down_predictions: int
    neutral_predictions: int


class AnalysisHistoryResponse(BaseModel):
    symbol: str
    period: str
    accuracy: AccuracyStats
    recent_predictions: List[PredictionRecord]
    generated_at: datetime
