from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from sqlmodel import Session

from app.shared.infrastructure.db import engine
from app.shared.infrastructure.ai.model_factory import get_sentiment_analyzer, get_market_reasoner
from app.modules.identity.public_api import get_current_user_dto, UserDTO
from app.shared.domain.enums import UserTier

from .dtos import CausalAnalysisResponse, ExplainPriceRequest, ExplainPriceResponse
from .handler import CausalHandler

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


def get_handler(session: Session = Depends(get_session)) -> CausalHandler:
    return CausalHandler(
        sentiment_analyzer=get_sentiment_analyzer(),
        reasoner=get_market_reasoner(),
        session=session,
    )


@router.get(
    "/{symbol}",
    response_model=CausalAnalysisResponse,
    summary="Get causal reasoning for price movement",
    description="Get AI-powered causal analysis explaining why a symbol's price moved. Requires VIP subscription.",
)
async def get_causal_analysis(
    symbol: str,
    from_time: Optional[datetime] = Query(default=None, alias="from", description="Start time (ISO 8601)"),
    to_time: Optional[datetime] = Query(default=None, alias="to", description="End time (ISO 8601)"),
    handler: CausalHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get causal analysis for a symbol's price movement.

    **Parameters:**
    - symbol: Trading pair (e.g., BTCUSDT)
    - from: Start time for analysis period (optional, defaults to 24h ago)
    - to: End time for analysis period (optional, defaults to now)

    **Returns:**
    - Price change details
    - Causal factors with impact scores
    - Category breakdown (REGULATORY, ON_CHAIN, MARKET, NEWS, TECHNICAL)
    - AI-generated summary
    """
    return await handler.get_causal_analysis(symbol.upper(), from_time, to_time)


@router.post(
    "/explain",
    response_model=ExplainPriceResponse,
    summary="Explain a specific price movement",
    description="Provide specific price data and get AI explanation. Requires VIP subscription.",
)
async def explain_price_movement(
    request: ExplainPriceRequest,
    handler: CausalHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Explain a specific price movement.

    **Request Body:**
    - symbol: Trading pair
    - price_from: Starting price
    - price_to: Ending price
    - period_from: Start time
    - period_to: End time
    - additional_context: (optional) Any additional context to consider

    **Returns:**
    - Causal factors explaining the movement
    - Confidence score
    - Summary
    """
    return await handler.explain_price_movement(request)
