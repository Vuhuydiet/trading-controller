from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.modules.identity.public_api import get_current_user_dto
from .handler import GetDepthHandler
from .dtos import VALID_LIMITS, DepthResponse

router = APIRouter()


@router.get(
    "/depth/{symbol}",
    response_model=DepthResponse,
    summary="Get order book depth",
    description=f"Retrieve real-time order book depth (bids and asks) for a trading pair. Valid limits: {', '.join(map(str, VALID_LIMITS))}"
)
async def get_order_book_depth(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    limit: int = Query(100, description=f"Number of orders to return. Valid: {', '.join(map(str, VALID_LIMITS))}"),
    user = Depends(get_current_user_dto)
):
    try:
        handler = GetDepthHandler()
        depth = await handler.handle(symbol, limit)
        return depth
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order book depth: {str(e)}")
