from fastapi import APIRouter, Depends
from typing import Optional
from app.modules.identity.optional_auth import get_current_user_optional
from app.modules.identity.public_api import UserDTO
from app.modules.market.infrastructure.binance_ws_manager import get_ws_manager
from app.modules.market.infrastructure.price_cache import get_price_cache

router = APIRouter()


@router.get(
    "/ws/status",
    summary="Get WebSocket connection status",
    description="Retrieve the current status of the WebSocket connection to Binance including connection state, subscribed streams, and cache statistics. Public endpoint - no authentication required."
)
async def get_websocket_status(user: Optional[UserDTO] = Depends(get_current_user_optional)):
    ws_manager = get_ws_manager()
    price_cache = get_price_cache()

    cached_prices = price_cache.get_all_prices()
    cached_tickers = price_cache.get_all_tickers()

    return {
        "connected": ws_manager.is_connected,
        "running": ws_manager.running,
        "subscribed_streams": list(ws_manager.subscribed_streams),
        "cached_prices_count": len(cached_prices),
        "cached_tickers_count": len(cached_tickers),
        "cached_symbols": list(cached_prices.keys())
    }
