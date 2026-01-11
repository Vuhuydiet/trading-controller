from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session
from typing import Optional, List
from app.shared.infrastructure.db import get_session
from app.modules.identity.optional_auth import get_current_user_optional, get_user_limits
from app.modules.identity.public_api import UserDTO
from .handler import GetKlinesHandler
from .dtos import VALID_INTERVALS, KlineResponse

router = APIRouter()


@router.get(
    "/klines/{symbol}",
    response_model=List[KlineResponse],
    summary="Get candlestick data by path parameter",
    description=f"Retrieve candlestick (OHLCV) data for a trading pair. Supports ISO 8601 timestamps and Unix milliseconds. Valid intervals: {', '.join(VALID_INTERVALS)}. Public endpoint - authentication optional. Limits: Anonymous=500, Free=500, VIP=5000."
)
async def get_klines_by_path(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    interval: str = Query(..., description=f"Kline interval. Valid: {', '.join(VALID_INTERVALS)}"),
    start_time: Optional[str] = Query(None, description="Start time (ISO 8601 or milliseconds)"),
    end_time: Optional[str] = Query(None, description="End time (ISO 8601 or milliseconds)"),
    limit: int = Query(500, ge=1, le=5000, description="Number of klines to return"),
    session: Session = Depends(get_session),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        # Apply tier-based limits
        user_limits = get_user_limits(user)
        max_klines = user_limits["max_klines"]

        # Cap the limit based on user tier
        if limit > max_klines:
            limit = max_klines

        handler = GetKlinesHandler(session)
        klines = await handler.handle(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return klines
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch klines: {str(e)}")


@router.get(
    "/klines",
    response_model=List[KlineResponse],
    summary="Get candlestick data by query parameter",
    description=f"Retrieve candlestick (OHLCV) data for a trading pair. Supports ISO 8601 timestamps and Unix milliseconds. Valid intervals: {', '.join(VALID_INTERVALS)}. Public endpoint - authentication optional. Limits: Anonymous=500, Free=500, VIP=5000."
)
async def get_klines_by_query(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    interval: str = Query(..., description=f"Kline interval. Valid: {', '.join(VALID_INTERVALS)}"),
    start_time: Optional[str] = Query(None, description="Start time (ISO 8601 or milliseconds)"),
    end_time: Optional[str] = Query(None, description="End time (ISO 8601 or milliseconds)"),
    limit: int = Query(500, ge=1, le=5000, description="Number of klines to return"),
    session: Session = Depends(get_session),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        # Apply tier-based limits
        user_limits = get_user_limits(user)
        max_klines = user_limits["max_klines"]

        # Cap the limit based on user tier
        if limit > max_klines:
            limit = max_klines

        handler = GetKlinesHandler(session)
        klines = await handler.handle(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return klines
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch klines: {str(e)}")
