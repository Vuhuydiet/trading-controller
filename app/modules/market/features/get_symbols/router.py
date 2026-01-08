from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List
from app.modules.identity.optional_auth import get_current_user_optional
from app.modules.identity.public_api import UserDTO
from .handler import GetSymbolsHandler, GetSymbolDetailHandler, GetSymbolInfoHandler
from .dtos import SymbolResponse, SymbolDetailResponse, SymbolInfoResponse

router = APIRouter()


@router.get(
    "/symbols",
    response_model=List[SymbolResponse],
    summary="List all trading symbols",
    description="Retrieve a list of all available trading pairs from Binance with optional filtering by quote asset and trading status. Public endpoint - no authentication required."
)
async def get_symbols(
    quote_asset: Optional[str] = Query(None, description="Filter by quote asset (e.g., USDT, BTC)"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., TRADING, BREAK)"),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetSymbolsHandler()
        symbols = await handler.handle(quote_asset=quote_asset, status=status)
        return symbols
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


@router.get(
    "/symbols/{symbol}",
    response_model=SymbolDetailResponse,
    summary="Get symbol details",
    description="Retrieve detailed information about a specific trading pair including precision, order types, and trading permissions. Public endpoint - no authentication required."
)
async def get_symbol_detail(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetSymbolDetailHandler()
        symbol_detail = await handler.handle(symbol)
        return symbol_detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbol detail: {str(e)}")


@router.get(
    "/symbols/{symbol}/info",
    response_model=SymbolInfoResponse,
    summary="Get complete symbol information",
    description="Retrieve comprehensive trading information for a symbol including all trading rules, filters, precision settings, and permissions. Public endpoint - no authentication required."
)
async def get_symbol_info(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        handler = GetSymbolInfoHandler()
        symbol_info = await handler.handle(symbol)
        return symbol_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbol info: {str(e)}")
