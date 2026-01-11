from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InsightResponse(BaseModel):
    """Response model for news insights"""

    id: Optional[str] = Field(default=None)
    article_id: str
    source: str
    cryptocurrency_mentioned: List[str] = Field(default_factory=list)
    sentiment: str
    sentiment_score: float = Field(ge=-1, le=1)
    key_points: List[str] = Field(default_factory=list)
    market_impact: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    summary: str
    processed_date: datetime
    llm_model_used: str

    class Config:
        from_attributes = True


class GetInsightsResponse(BaseModel):
    """Response model for insights endpoint"""

    insights: List[InsightResponse]
    total: int = Field(description="Total insights returned")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GetInsightByArticleRequest(BaseModel):
    """Request model for getting insight by article ID"""

    article_id: str = Field(..., description="Article ID")
