"""News API Router"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.shared.infrastructure.db import get_session
from app.modules.news.features.dtos import (
    NewsDetailResponse,
    NewsListResponse,
)
from app.modules.news.features.handler import NewsHandler

router = APIRouter()


class NewsSource(str, Enum):
    """Available news sources"""
    COINDESK = "coindesk"
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    TWITTER = "twitter"


class CryptoSymbol(str, Enum):
    """Supported cryptocurrency symbols"""
    BTCUSDT = "BTCUSDT"
    ETHUSDT = "ETHUSDT"
    BNBUSDT = "BNBUSDT"
    XRPUSDT = "XRPUSDT"
    SOLUSDT = "SOLUSDT"
    ADAUSDT = "ADAUSDT"
    DOGEUSDT = "DOGEUSDT"
    DOTUSDT = "DOTUSDT"
    MATICUSDT = "MATICUSDT"
    LTCUSDT = "LTCUSDT"


@router.get(
    "",
    response_model=NewsListResponse,
    summary="Get News",
    description="""
Get paginated news articles with flexible filtering options.

**Examples:**
- Get all news: `GET /news`
- Search by keyword: `GET /news?q=bitcoin`
- Filter by symbol: `GET /news?symbol=BTCUSDT`
- Filter by source: `GET /news?source=coindesk`
- Combined filters: `GET /news?q=price&symbol=BTCUSDT&source=bloomberg`
- Date range: `GET /news?from_date=2024-01-01&to_date=2024-01-31`
""",
)
async def get_news(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=50, description="Items per page"),
    q: Optional[str] = Query(
        default=None,
        min_length=2,
        description="Search keyword in title and content",
        examples=["bitcoin", "ethereum", "crypto market", "SEC regulation", "price surge"],
    ),
    symbol: Optional[CryptoSymbol] = Query(
        default=None,
        description="Filter by cryptocurrency symbol (e.g., BTCUSDT searches for 'bitcoin', 'btc')",
    ),
    source: Optional[NewsSource] = Query(
        default=None,
        description="Filter by news source",
    ),
    from_date: Optional[datetime] = Query(
        default=None,
        description="Filter news from this date (ISO format)",
        examples=["2024-01-01T00:00:00"],
    ),
    to_date: Optional[datetime] = Query(
        default=None,
        description="Filter news until this date (ISO format)",
        examples=["2024-12-31T23:59:59"],
    ),
    session: Session = Depends(get_session),
):
    """
    Unified news endpoint with flexible filtering.

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 50)
    - **q**: Search keyword (searches in title and content, case-insensitive)
    - **symbol**: Filter by crypto symbol (BTCUSDT, ETHUSDT, etc.)
    - **source**: Filter by news source (coindesk, reuters, bloomberg, twitter)
    - **from_date**: Filter news published after this date
    - **to_date**: Filter news published before this date
    """
    handler = NewsHandler(session)
    return await handler.get_news(
        page=page,
        limit=limit,
        q=q,
        symbol=symbol.value if symbol else None,
        source=source.value if source else None,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/sources",
    response_model=List[dict],
    summary="Get Available Sources",
    description="Get list of available news sources",
)
async def get_news_sources():
    """
    Get list of available news sources.
    """
    return [
        {"id": "coindesk", "name": "CoinDesk", "description": "Leading crypto news"},
        {"id": "reuters", "name": "Reuters", "description": "Global news agency"},
        {"id": "bloomberg", "name": "Bloomberg", "description": "Financial news"},
        {"id": "twitter", "name": "Twitter/X", "description": "Social media posts"},
    ]


@router.get(
    "/{news_id:path}",
    response_model=NewsDetailResponse,
    summary="Get News Detail",
    description="Get detailed news article with full content and analysis",
)
async def get_news_detail(
    news_id: str,
    session: Session = Depends(get_session),
):
    """
    Get detailed news article by ID.

    - **news_id**: News unique identifier (URL-encoded if contains special chars)
    """
    # Decode URL-encoded news_id
    decoded_id = unquote(news_id)
    handler = NewsHandler(session)
    result = await handler.get_news_detail(news_id=decoded_id)

    if not result:
        raise HTTPException(status_code=404, detail="News not found")

    return result
