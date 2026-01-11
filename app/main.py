from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

# Import router từ từng Feature slice
from app.modules.identity.features.register.router import router as register_router
from app.modules.identity.features.login.router import router as login_router
from app.modules.identity.features.forgot_password.router import router as forgot_pass_router
from app.modules.identity.features.refresh_token.router import router as refresh_router
from app.modules.identity.features.get_me.router import router as get_me_router

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

from app.modules.news.public_api import get_news_router, get_insights_router

from app.modules.subscription.features.get_plans.router import router as plans_router
from app.modules.subscription.features.buy_subscription.router import router as buy_sub_router

from app.shared.core.logging_config import setup_logging
from app.shared.infrastructure.db import create_db_and_tables, Session, engine
from app.modules.subscription.infrastructure.seeder import seed_plans
from app.modules.news.infrastructure.mongo_connection import MongoDB
from app.modules.news.infrastructure.pipeline import NewsPipeline
from app.modules.news.infrastructure.repository import MongoNewsRepository, MongoInsightRepository
from app.modules.news.domain.services import NewsService
from app.modules.news.infrastructure.crawlers import (
    CoinDeskCrawler,
    ReutersCrawler,
    BloombergCrawler,
    TwitterCrawler,
)
from app.modules.news.infrastructure.llm_adapter import get_llm_adapter
from app.modules.news.domain.article import NewsSource

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo Database & Seed Data
    print("Starting up database...")
    create_db_and_tables()
    with Session(engine) as session:
        seed_plans(session)

    # Khởi tạo MongoDB cho News Module
    print("Connecting to MongoDB...")
    try:
        await MongoDB.connect()

        # Initialize News Pipeline
        db = MongoDB.get_db()
        news_repo = MongoNewsRepository(db)
        insight_repo = MongoInsightRepository(db)

        crawlers: Dict[NewsSource, Any] = {
            NewsSource.COINDESK: CoinDeskCrawler(),
            NewsSource.REUTERS: ReutersCrawler(),
            NewsSource.BLOOMBERG: BloombergCrawler(),
            NewsSource.TWITTER: TwitterCrawler(),
        }

        llm_adapter = get_llm_adapter()
        news_service = NewsService(news_repo, insight_repo, crawlers, llm_adapter)

        await NewsPipeline.initialize(news_service)
        await NewsPipeline.start()
        print("News pipeline started successfully")
    except Exception as e:
        print(f"Warning: Could not initialize MongoDB for News Module: {e}")

    # Khởi động WebSocket Manager
    print("Starting WebSocket manager...")
    ws_manager = get_ws_manager()
    streams = get_default_streams()
    await ws_manager.start(streams)

    yield

    print("Shutting down WebSocket manager...")
    await ws_manager.stop()

    print("Shutting down News pipeline...")
    await NewsPipeline.stop()

    print("Disconnecting from MongoDB...")
    await MongoDB.disconnect()

# Khởi tạo app với lifespan đã gộp
app = FastAPI(lifespan=lifespan, title="Modular Monolith Trading")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register_router, prefix="/api/v1", tags=["auth"])
app.include_router(login_router, prefix="/api/v1", tags=["auth"])
app.include_router(forgot_pass_router, prefix="/api/v1", tags=["auth"])
app.include_router(refresh_router, prefix="/api/v1", tags=["auth"])
app.include_router(get_me_router, prefix="/api/v1", tags=["auth"])

app.include_router(plans_router, prefix="/api/v1", tags=["subscription"])
app.include_router(buy_sub_router, prefix="/api/v1", tags=["subscription"])

app.include_router(chart_router, prefix="/api/v1", tags=["market"])
app.include_router(klines_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(ticker_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(price_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(depth_router, prefix="/api/v1/market", tags=["market-data"])
app.include_router(stream_router, prefix="/api/v1/market", tags=["market-data-stream"])
app.include_router(symbols_router, prefix="/api/v1/market", tags=["market-symbols"])
app.include_router(ws_status_router, prefix="/api/v1/market", tags=["market-websocket"])

app.include_router(get_news_router, prefix="/api/v1/news", tags=["news"])
app.include_router(get_insights_router, prefix="/api/v1/news", tags=["news-insights"])

@app.get("/")
def root():
    return {"message": "System is running with Modular Monolith Architecture"}
