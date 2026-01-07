from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# Đây là Table trong database
class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: str = Field(index=True) # ID của bản tin
    sentiment: str                   # positive/negative
    confidence: float                # 0.95
    reasoning: str                   # Text giải thích dài
    created_at: datetime = Field(default_factory=datetime.utcnow)