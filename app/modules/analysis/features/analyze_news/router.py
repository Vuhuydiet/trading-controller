from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.shared.infrastructure.db import engine
from app.shared.core.config import settings
from .dtos import AnalyzeNewsRequest, AnalyzeNewsResponse
from .handler import AnalyzeNewsHandler

# Import Domain Services
from app.modules.analysis.domain.services import NewsPriceAligner

# Import Infrastructure - Model Factory (Config-based)
from app.shared.infrastructure.ai.model_factory import get_sentiment_analyzer, get_market_reasoner
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo

# Import Authentication
from app.modules.identity.public_api import get_current_user_dto, UserDTO
from app.shared.domain.enums import UserTier

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def get_handler(session: Session = Depends(get_session)) -> AnalyzeNewsHandler:
    """
    Get handler with AI models loaded from config.

    Models are determined by .env settings:
    - AI_SENTIMENT_MODEL: finbert | openai | ensemble
    - AI_REASONING_PROVIDER: ollama | openai | gemini
    - AI_REASONING_MODEL: llama3.2 | gpt-4 | gemini-pro
    """
    return AnalyzeNewsHandler(
        sentiment_bot=get_sentiment_analyzer(),
        reasoning_bot=get_market_reasoner(),
        repo=SqlModelAnalysisRepo(session),
        aligner=NewsPriceAligner()
    )

def require_vip_access(user: UserDTO = Depends(get_current_user_dto)) -> UserDTO:
    """
    Require VIP tier for AI analysis features.
    Raises 403 Forbidden if user is not VIP.
    """
    if user.tier != UserTier.VIP:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "AI Analysis requires VIP subscription",
                "current_tier": user.tier,
                "required_tier": "VIP",
                "message": "Please upgrade to VIP to access AI-powered analysis features"
            }
        )
    return user

@router.post(
    "",
    response_model=AnalyzeNewsResponse,
    summary="Analyze news with AI",
    description="Analyze crypto news using AI sentiment analysis and trend prediction. Requires VIP subscription."
)
async def analyze_news(
    body: AnalyzeNewsRequest,
    handler: AnalyzeNewsHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access)
):
    """
    Analyze news content with AI-powered sentiment and trend prediction.

    **Authentication Required**: VIP tier only

    **Features**:
    - Sentiment analysis (positive/negative/neutral)
    - Market trend prediction (UP/DOWN/NEUTRAL)
    - AI-generated reasoning

    **Models Used**:
    - FinBERT for sentiment analysis
    - Llama 3.2 for trend reasoning
    """
    return await handler.execute(body)