from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlmodel import Session

from app.shared.infrastructure.db import engine
from app.shared.infrastructure.ai.model_factory import get_sentiment_analyzer, get_market_reasoner
from app.modules.identity.public_api import get_current_user_dto, UserDTO
from app.shared.domain.enums import UserTier

from .dtos import SymbolPredictionResponse, MultiPredictionResponse
from .handler import PredictionHandler

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


def get_handler(session: Session = Depends(get_session)) -> PredictionHandler:
    return PredictionHandler(
        sentiment_analyzer=get_sentiment_analyzer(),
        reasoner=get_market_reasoner(),
        session=session,
    )


@router.get(
    "/{symbol}",
    response_model=SymbolPredictionResponse,
    summary="Get AI price trend prediction",
    description="Get AI-powered price trend prediction for a specific symbol. Requires VIP subscription.",
)
async def get_symbol_prediction(
    symbol: str,
    timeframe: str = Query(default="24h", pattern="^(1h|4h|24h|7d)$", description="Prediction timeframe"),
    handler: PredictionHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get AI price trend prediction for a symbol.

    **Parameters:**
    - symbol: Trading pair (e.g., BTCUSDT)
    - timeframe: Prediction timeframe (1h, 4h, 24h, 7d)

    **Returns:**
    - Predicted direction (UP/DOWN/NEUTRAL)
    - Confidence score
    - Target price ranges
    - Support and resistance levels
    """
    return await handler.get_symbol_prediction(symbol.upper(), timeframe)


@router.get(
    "",
    response_model=MultiPredictionResponse,
    summary="Get predictions for multiple symbols",
    description="Get AI-powered predictions for multiple trading symbols. Requires VIP subscription.",
)
async def get_multi_predictions(
    symbols: str = Query(
        default="BTCUSDT,ETHUSDT,SOLUSDT",
        description="Comma-separated list of symbols"
    ),
    timeframe: str = Query(default="24h", pattern="^(1h|4h|24h|7d)$", description="Prediction timeframe"),
    handler: PredictionHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get predictions for multiple symbols.

    **Parameters:**
    - symbols: Comma-separated list of trading pairs
    - timeframe: Prediction timeframe (1h, 4h, 24h, 7d)

    **Returns:**
    - List of predictions for each symbol
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    if len(symbol_list) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 symbols allowed per request"
        )
    return await handler.get_multi_predictions(symbol_list, timeframe)
