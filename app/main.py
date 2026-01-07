from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.shared.core.logging_config import setup_logging

setup_logging()

# Import router từ từng Feature slice
from app.modules.identity.features.register.router import router as register_router
from app.modules.identity.features.login.router import router as login_router
from app.modules.market.features.get_ai_analysis.router import router as ai_router
from app.modules.market.features.check_chart_access.router import router as chart_router
from app.modules.market.features.get_klines.router import router as klines_router
from app.modules.market.features.get_ticker.router import router as ticker_router
from app.modules.market.features.stream_market_data.router import router as stream_router
from app.modules.market.features.get_symbols.router import router as symbols_router
from app.modules.market.features.get_price.router import router as price_router
from app.modules.market.features.get_depth.router import router as depth_router
from app.modules.market.features.ws_status.router import router as ws_status_router
from app.modules.market.infrastructure.binance_ws_manager import get_ws_manager
from app.modules.market.infrastructure.ws_config import get_default_streams


@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager = get_ws_manager()
    streams = get_default_streams()
    await ws_manager.start(streams)
    yield
    await ws_manager.stop()


app = FastAPI(title="Modular Monolith Trading", lifespan=lifespan)


app.include_router(register_router, prefix="/api/v1", tags=["auth"])
app.include_router(login_router, prefix="/api/v1", tags=["auth"])

app.include_router(ai_router, prefix="/api/v1", tags=["market"])
app.include_router(chart_router, prefix="/api/v1", tags=["market"])
app.include_router(klines_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(ticker_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(price_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(depth_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(stream_router, prefix="/api/v1/market", tags=["market-data-stream"])
app.include_router(symbols_router, prefix="/api/v1/market", tags=["market-symbols"])
app.include_router(ws_status_router, prefix="/api/v1/market", tags=["market-websocket"])

@app.get("/")
def root():
    return {"message": "System is running with Modular Monolith Architecture"}