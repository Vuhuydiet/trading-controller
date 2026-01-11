from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session
from typing import Optional, List
from app.shared.infrastructure.db import get_session
from app.modules.identity.optional_auth import get_current_user_optional
from app.modules.identity.public_api import UserDTO
from .handler import GetTickerHandler, GetTickersHandler
from .dtos import TickerResponse, TickersResponse

router = APIRouter()


@router.get(
    "/ticker/{symbol}",
    response_model=TickerResponse,
    summary="Get 24hr ticker statistics by path parameter",
    description="Retrieve 24-hour rolling window price change statistics for a trading pair including price change, volume, high/low, and bid/ask prices. Public endpoint - no authentication required."
)
async def get_ticker_by_path(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    session: Session = Depends(get_session),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetTickerHandler(session)
        ticker = await handler.handle(symbol)
        return ticker
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get(
    "/ticker",
    response_model=TickerResponse,
    summary="Get 24hr ticker statistics by query parameter",
    description="Retrieve 24-hour rolling window price change statistics for a trading pair including price change, volume, high/low, and bid/ask prices. Public endpoint - no authentication required."
)
async def get_ticker_by_query(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    session: Session = Depends(get_session),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetTickerHandler(session)
        ticker = await handler.handle(symbol)
        return ticker
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get(
    "/tickers",
    response_model=TickersResponse,
    summary="Get 24hr ticker statistics for multiple symbols",
    description="Retrieve 24-hour rolling window price change statistics for multiple trading pairs or all symbols if no filter is provided. Public endpoint - no authentication required."
)
async def get_tickers(
    symbols: Optional[List[str]] = Query(None, description="List of symbols (e.g., BTCUSDT,ETHUSDT)"),
    session: Session = Depends(get_session),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetTickersHandler(session)
        tickers = await handler.handle(symbols)
        return tickers
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {str(e)}")
