from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.shared.infrastructure.db import engine
from app.shared.core.config import settings
from .dtos import AnalyzeNewsRequest, AnalyzeNewsResponse
from .handler import AnalyzeNewsHandler
from app.shared.infrastructure.db import get_session
from app.modules.analysis.features.analyze_news.dtos import NewsFeedResponse, NewsFeedItem, AnalysisSummary, BatchAnalysisResponse

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

@router.get("/feed", response_model=NewsFeedResponse)
async def get_market_news_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    session: Session = Depends(get_session)
):
    """
    API News Feed cho Frontend: Trả về tin tức + Màu xanh đỏ (Sentiment)
    """
    repo = SqlModelAnalysisRepo(session)
    offset = (page - 1) * limit
    
    # 1. Query DB
    news_list = await repo.get_news_feed(limit, offset)
    total = await repo.count_news()

    # 2. Map Entity -> DTO
    items = []
    for news in news_list:
        # Map phần Analysis (nếu có)
        ai_data = None
        if news.analysis:
            ai_data = AnalysisSummary(
                sentiment=news.analysis.sentiment, # VD: BULLISH
                score=news.analysis.confidence,
                trend=news.analysis.trend
            )
        
        # Map phần News
        items.append(NewsFeedItem(
            id=news.news_id,
            title=news.title,
            source=news.source,
            published_at=news.published_at,
            summary=news.content[:200] + "...", # Cắt ngắn làm summary
            analysis=ai_data
        ))

    return NewsFeedResponse(items=items, total=total)


@router.post("/batch", response_model=BatchAnalysisResponse)
async def batch_analyze_news(
    limit: int = Query(10, ge=1, le=50, description="Max number of news to analyze"),
    session: Session = Depends(get_session),
    user: UserDTO = Depends(require_vip_access)
):
    """
    Batch analyze all news that don't have analysis yet.

    **Authentication Required**: VIP tier only

    This endpoint will:
    1. Find news without analysis (up to limit)
    2. Run AI sentiment + reasoning on each
    3. Save results to database
    4. Return summary

    Note: This may take a while depending on the number of news items.
    """
    repo = SqlModelAnalysisRepo(session)

    # Get news without analysis
    pending_news = await repo.get_news_without_analysis(limit)

    if not pending_news:
        return BatchAnalysisResponse(
            total_pending=0,
            analyzed=0,
            failed=0,
            results=[]
        )

    # Initialize AI models once
    sentiment_analyzer = get_sentiment_analyzer()
    market_reasoner = get_market_reasoner()
    aligner = NewsPriceAligner()

    analyzed = 0
    failed = 0
    results = []

    for news in pending_news:
        try:
            handler = AnalyzeNewsHandler(
                sentiment_bot=sentiment_analyzer,
                reasoning_bot=market_reasoner,
                repo=SqlModelAnalysisRepo(session),
                aligner=aligner
            )

            request = AnalyzeNewsRequest(
                news_id=news.news_id,
                news_content=news.content or news.title,
                published_at=news.published_at
            )

            result = await handler.execute(request)
            analyzed += 1
            results.append({
                "news_id": news.news_id,
                "title": news.title[:50] + "...",
                "sentiment": result.sentiment,
                "trend": result.trend,
                "status": "success"
            })
        except Exception as e:
            failed += 1
            results.append({
                "news_id": news.news_id,
                "title": news.title[:50] + "...",
                "error": str(e),
                "status": "failed"
            })

    return BatchAnalysisResponse(
        total_pending=len(pending_news),
        analyzed=analyzed,
        failed=failed,
        results=results
    )