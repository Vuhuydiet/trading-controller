from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    news_id: str
    news_content: str
    price_change_24h: float

class AnalysisResponse(BaseModel):
    sentiment: str
    confidence: float
    reasoning: str

from pydantic import BaseModel
from datetime import datetime

class AnalyzeNewsRequest(BaseModel):
    news_id: str
    news_content: str
    published_at: datetime # Cần cái này để tìm giá lịch sử

class AnalyzeNewsResponse(BaseModel):
    sentiment: str
    confidence: float
    reasoning: str