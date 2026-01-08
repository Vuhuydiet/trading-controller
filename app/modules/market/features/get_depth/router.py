from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional
from app.modules.identity.optional_auth import get_current_user_optional, get_user_limits
from app.modules.identity.public_api import UserDTO
from .handler import GetDepthHandler
from .dtos import VALID_LIMITS, DepthResponse

router = APIRouter()


@router.get(
    "/depth/{symbol}",
    response_model=DepthResponse,
    summary="Get order book depth",
    description=f"Retrieve real-time order book depth (bids and asks) for a trading pair. Valid limits: {', '.join(map(str, VALID_LIMITS))}. Public endpoint - authentication optional. Max depth: Anonymous=100, Free=100, VIP=1000."
)
async def get_order_book_depth(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    limit: int = Query(100, description=f"Number of orders to return. Valid: {', '.join(map(str, VALID_LIMITS))}"),
    user: Optional[UserDTO] = Depends(get_current_user_optional)
):
    try:
        # Apply tier-based limits
        user_limits = get_user_limits(user)
        max_depth = user_limits["max_depth"]

        # Validate limit is in VALID_LIMITS
        if limit not in VALID_LIMITS:
            # Find closest valid limit
            limit = min(VALID_LIMITS, key=lambda x: abs(x - limit))

        # Cap the limit based on user tier
        if limit > max_depth:
            limit = min([l for l in VALID_LIMITS if l <= max_depth], default=VALID_LIMITS[0])

        handler = GetDepthHandler()
        depth = await handler.handle(symbol, limit)
        return depth
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order book depth: {str(e)}")
