from fastapi import BackgroundTasks
from sqlmodel import Session
from app.shared.infrastructure.db import engine
from app.modules.analysis.features.analyze_news.handler import AnalyzeNewsHandler
from app.modules.analysis.features.analyze_news.dtos import AnalyzeNewsRequest

# Import các dependency cần thiết (y chang trong Router)
from app.modules.analysis.domain.services import NewsPriceAligner
from app.shared.infrastructure.ai.sentiment_adapter import get_finbert_adapter_instance
from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo
from app.shared.core.config import settings

# Hàm này sẽ được chạy ngầm
async def _run_analysis_task(news_id: str, content: str, published_at):
    with Session(engine) as session:
        # Tự khởi tạo Handler (Manual Wiring)
        handler = AnalyzeNewsHandler(
            sentiment_bot=get_finbert_adapter_instance(),
            reasoning_bot=OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL),
            repo=SqlModelAnalysisRepo(session),
            aligner=NewsPriceAligner()
        )
        
        # Tạo request giả lập
        req = AnalyzeNewsRequest(
            news_id=news_id, 
            news_content=content, 
            published_at=published_at
        )
        
        print(f"[Background] Starting AI Analysis for news: {news_id}")
        await handler.execute(req)
        print(f"[Background] Finished AI Analysis for news: {news_id}")

def trigger_analysis_background(
    background_tasks: BackgroundTasks, 
    news_id: str, 
    content: str, 
    published_at
):
    """
    Hàm này không chạy AI ngay, mà chỉ 'đăng ký' task vào hàng đợi background.
    Nó trả về ngay lập tức (Non-blocking).
    """
    background_tasks.add_task(_run_analysis_task, news_id, content, published_at)