from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.shared.infrastructure.db import engine
from app.shared.core.config import settings
from .dtos import AnalyzeNewsRequest, AnalyzeNewsResponse
from .handler import AnalyzeNewsHandler

# Import Domain Services
from app.modules.analysis.domain.services import NewsPriceAligner

# Import Infrastructure Adapters (Gateway)
from app.shared.infrastructure.ai.sentiment_adapter import get_finbert_adapter_instance
from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def get_handler(session: Session = Depends(get_session)) -> AnalyzeNewsHandler:
    return AnalyzeNewsHandler(
        sentiment_bot=get_finbert_adapter_instance(),
        
        reasoning_bot=OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL),
        repo=SqlModelAnalysisRepo(session),
        aligner=NewsPriceAligner()
    )

@router.post("/ai-analysis", response_model=AnalyzeNewsResponse)
async def analyze_news(
    body: AnalyzeNewsRequest,
    handler: AnalyzeNewsHandler = Depends(get_handler)
):
    return await handler.execute(body)