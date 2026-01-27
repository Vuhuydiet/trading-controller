from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

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

# Phần Analysis con
class AnalysisSummary(BaseModel):
    sentiment: str
    score: float
    trend: str

# Object tổng hợp trả về FE
class NewsFeedItem(BaseModel):
    id: str # news_id
    title: str
    source: str
    published_at: datetime
    summary: str # Cắt ngắn content
    
    # 👇 Kèm theo phân tích (Optional vì có thể có bài chưa kịp phân tích)
    analysis: Optional[AnalysisSummary] = None

class NewsFeedResponse(BaseModel):
    items: List[NewsFeedItem]
    total: int


# Batch Analysis Response
class BatchAnalysisResponse(BaseModel):
    total_pending: int
    analyzed: int
    failed: int
    results: List[dict]