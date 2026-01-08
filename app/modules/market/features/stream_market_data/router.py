from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional
import json
from app.modules.identity.public_api import get_current_user_dto
from .handler import StreamMarketDataHandler

router = APIRouter()


@router.websocket("/ws/market")
async def websocket_market_data(
    websocket: WebSocket,
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    stream_type: str = Query(..., description="Stream type: kline, ticker, trade, depth"),
    interval: Optional[str] = Query(None, description="Kline interval (required for kline stream)")
):
    await websocket.accept()

    handler = StreamMarketDataHandler()

    async def send_to_client(data):
        try:
            await websocket.send_json(data)
        except Exception:
            await handler.disconnect()

    try:
        if stream_type == "kline":
            if not interval:
                await websocket.send_json({"error": "interval is required for kline stream"})
                await websocket.close()
                return
            await handler.stream_klines(symbol, interval, send_to_client)
        elif stream_type == "ticker":
            await handler.stream_ticker(symbol, send_to_client)
        elif stream_type == "trade":
            await handler.stream_trades(symbol, send_to_client)
        elif stream_type == "depth":
            await handler.stream_depth(symbol, send_to_client)
        else:
            await websocket.send_json({"error": f"Unknown stream type: {stream_type}"})
            await websocket.close()

    except WebSocketDisconnect:
        await handler.disconnect()
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await handler.disconnect()
        await websocket.close()
