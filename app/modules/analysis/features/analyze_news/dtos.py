from pydantic import BaseModel
from datetime import datetime

# Input: Chỉ cần tin tức và thời gian (để Aligner tự làm việc)
class AnalyzeNewsRequest(BaseModel):
    news_id: str
    news_content: str
    published_at: datetime 

# Output: Đầy đủ 4 món ăn chơi (Sentiment, Confidence, Trend, Reasoning)
class AnalyzeNewsResponse(BaseModel):
    sentiment: str
    confidence: float
    trend: str
    reasoning: str