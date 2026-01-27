"""News API Router"""

from datetime import datetime
from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.shared.infrastructure.db import get_session
from app.modules.news.features.dtos import (
    NewsBySymbolResponse,
    NewsDetailResponse,
    NewsItemResponse,
    NewsListResponse,
)
from app.modules.news.features.handler import NewsHandler

router = APIRouter()


@router.get(
    "",
    response_model=NewsListResponse,
    summary="Get News List",
    description="Get paginated list of news articles with optional source filter",
)
async def get_news_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=50, description="Items per page"),
    source: Optional[str] = Query(default=None, description="Filter by news source"),
    session: Session = Depends(get_session),
):
    """
    Get paginated news list.

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 50)
    - **source**: Optional filter by source (coindesk, reuters, bloomberg, twitter)
    """
    handler = NewsHandler(session)
    return await handler.get_news_list(page=page, limit=limit, source=source)


@router.get(
    "/search",
    response_model=dict,
    summary="Search News",
    description="Search news by keyword with optional filters",
)
async def search_news(
    q: str = Query(..., min_length=2, description="Search query"),
    source: Optional[str] = Query(default=None, description="Filter by source"),
    from_date: Optional[datetime] = Query(default=None, description="From date"),
    to_date: Optional[datetime] = Query(default=None, description="To date"),
    limit: int = Query(default=20, ge=1, le=50, description="Max results"),
    session: Session = Depends(get_session),
):
    """
    Search news articles by keyword.

    - **q**: Search query (min 2 characters)
    - **source**: Optional filter by source
    - **from_date**: Optional start date filter
    - **to_date**: Optional end date filter
    - **limit**: Maximum number of results (default: 20)
    """
    handler = NewsHandler(session)
    items, total = await handler.search_news(
        query=q, source=source, from_date=from_date, to_date=to_date, limit=limit
    )
    return {"items": items, "total": total, "query": q}


@router.get(
    "/by-symbol/{symbol}",
    response_model=NewsBySymbolResponse,
    summary="Get News by Symbol",
    description="Get news related to a specific cryptocurrency symbol",
)
async def get_news_by_symbol(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
    session: Session = Depends(get_session),
):
    """
    Get news related to a specific cryptocurrency symbol.

    - **symbol**: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
    - **limit**: Maximum number of results (default: 10)
    """
    handler = NewsHandler(session)
    return await handler.get_news_by_symbol(symbol=symbol.upper(), limit=limit)


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
