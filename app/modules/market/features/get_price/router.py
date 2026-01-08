from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, List
from app.modules.identity.public_api import get_current_user_dto
from .handler import GetPriceHandler, GetPricesHandler
from .dtos import PriceResponse, PricesResponse

router = APIRouter()


@router.get(
    "/price/{symbol}",
    response_model=PriceResponse,
    summary="Get current price for a symbol",
    description="Retrieve the latest price for a trading pair from WebSocket cache (real-time) or Binance API."
)
async def get_price(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    user = Depends(get_current_user_dto)
):
    try:
        handler = GetPriceHandler()
        price = await handler.handle(symbol)
        return price
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price: {str(e)}")


@router.get(
    "/prices",
    response_model=PricesResponse,
    summary="Get current prices for multiple symbols",
    description="Retrieve the latest prices for multiple trading pairs from WebSocket cache (real-time) or Binance API."
)
async def get_prices(
    symbols: Optional[List[str]] = Query(None, description="List of symbols (e.g., BTCUSDT,ETHUSDT)"),
    user = Depends(get_current_user_dto)
):
    try:
        handler = GetPricesHandler()
        prices = await handler.handle(symbols)
        return prices
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prices: {str(e)}")
