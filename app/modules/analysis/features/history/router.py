from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.shared.infrastructure.db import engine
from app.modules.identity.public_api import get_current_user_dto, UserDTO
from app.shared.domain.enums import UserTier

from .dtos import AnalysisHistoryResponse
from .handler import HistoryHandler

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


def get_handler(session: Session = Depends(get_session)) -> HistoryHandler:
    return HistoryHandler(session=session)


@router.get(
    "/{symbol}",
    response_model=AnalysisHistoryResponse,
    summary="Get historical predictions and accuracy",
    description="Get historical AI predictions and their accuracy for a symbol. Requires VIP subscription.",
)
async def get_analysis_history(
    symbol: str,
    period: str = Query(
        default="30d",
        pattern="^(7d|30d|90d|all)$",
        description="History period"
    ),
    handler: HistoryHandler = Depends(get_handler),
    user: UserDTO = Depends(require_vip_access),
):
    """
    Get historical predictions and accuracy.

    **Parameters:**
    - symbol: Trading pair (e.g., BTCUSDT)
    - period: History period (7d, 30d, 90d, all)

    **Returns:**
    - Accuracy statistics
    - Recent prediction records with verification status
    """
    return await handler.get_analysis_history(symbol.upper(), period)
