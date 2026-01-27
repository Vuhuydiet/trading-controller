from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.shared.infrastructure.db import engine
from app.shared.infrastructure.ai.model_factory import get_sentiment_analyzer, get_market_reasoner
from app.modules.identity.public_api import get_current_user_dto, UserDTO
from app.shared.domain.enums import UserTier

from .dtos import (
    SymbolSentimentResponse,
    MarketSentimentResponse,
    NewsSentimentResponse,
    AnalyzeSentimentNewsRequest,
)
from .handler import SentimentHandler

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


def require_vip_access(user: UserDTO = Depends(get_current_user_dto)) -> UserDTO:
    """Require VIP tier for AI analysis features"""
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


def get_handler(session: Session = Depends(get_session)) -> SentimentHandler:
    return SentimentHandler(
        sentiment_analyzer=get_sentiment_analyzer(),
        reasoner=get_market_reasoner(),
        session=session,
    )


# IMPORTANT: Static routes must be defined BEFORE dynamic routes to avoid conflicts
# "/market" must come before "/{symbol}"

@router.get(
    "/market",
    response_model=MarketSentimentResponse,
    summary="Get overall market sentiment",
    description="Get AI-powered overall cryptocurrency market sentiment. Requires VIP subscription.",
)
async def get_market_sentiment(
    period: str = Query(default="24h", pattern="^(1h|4h|24h|7d)$", description="Analysis period"),
    handler: SentimentHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get overall market sentiment.

    **Parameters:**
    - period: Time period for analysis (1h, 4h, 24h, 7d)

    **Returns:**
    - Overall sentiment score and label
    - Market-wide sentiment breakdown
    - Top movers with sentiment
    """
    return await handler.get_market_sentiment(period)


@router.post(
    "/news",
    response_model=NewsSentimentResponse,
    summary="Analyze sentiment of specific news",
    description="Analyze sentiment of provided news content. Requires VIP subscription.",
)
async def analyze_news_sentiment(
    request: AnalyzeSentimentNewsRequest,
    handler: SentimentHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Analyze sentiment of specific news content.

    **Request Body:**
    - news_content: The news text to analyze
    - symbol: (optional) Related trading symbol

    **Returns:**
    - Sentiment analysis result
    - Key phrases extracted
    - Affected cryptocurrency symbols
    """
    return await handler.analyze_news_sentiment(request)


@router.get(
    "/{symbol}",
    response_model=SymbolSentimentResponse,
    summary="Get sentiment analysis for symbol",
    description="Get AI-powered sentiment analysis for a specific trading symbol. Requires VIP subscription.",
)
async def get_symbol_sentiment(
    symbol: str,
    period: str = Query(default="24h", pattern="^(1h|4h|24h|7d)$", description="Analysis period"),
    handler: SentimentHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get sentiment analysis for a specific symbol.

    **Parameters:**
    - symbol: Trading pair (e.g., BTCUSDT)
    - period: Time period for analysis (1h, 4h, 24h, 7d)

    **Returns:**
    - Sentiment score and label
    - Breakdown of positive/neutral/negative mentions
    - Top factors affecting sentiment
    """
    return await handler.get_symbol_sentiment(symbol.upper(), period)
