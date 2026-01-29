"""Handler for News API operations"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlmodel import Session, col, select, func, or_

from app.modules.analysis.domain.entities import AnalysisResult, CachedNews
from app.modules.news.features.dtos import (
    NewsAnalysisResponse,
    NewsBySymbolResponse,
    NewsDetailResponse,
    NewsItemResponse,
    NewsListResponse,
)

logger = logging.getLogger(__name__)


class NewsHandler:
    """Handler for news-related operations"""

    def __init__(self, session: Session):
        self.session = session

    def _to_news_item(self, news: CachedNews) -> NewsItemResponse:
        """Convert CachedNews entity to NewsItemResponse"""
        analysis = None
        if news.analysis:
            analysis = NewsAnalysisResponse(
                sentiment=news.analysis.sentiment,
                confidence=news.analysis.confidence,
                trend=news.analysis.trend,
                reasoning=news.analysis.reasoning,
            )

        return NewsItemResponse(
            id=news.news_id,
            title=news.title,
            source=news.source,
            url=news.news_id,  # news_id stores the original article URL
            content=news.content[:500] if len(news.content) > 500 else news.content,
            published_at=news.published_at,
            analysis=analysis,
        )

    async def get_news(
        self,
        page: int = 1,
        limit: int = 20,
        q: Optional[str] = None,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> NewsListResponse:
        """
        Unified news query with flexible filtering.
        Combines list, search, and by-symbol functionality.
        """
        offset = (page - 1) * limit

        # Build base query
        query = select(CachedNews)
        count_query = select(func.count()).select_from(CachedNews)

        conditions = []

        # Search by keyword (q)
        if q:
            search_condition = or_(
                col(CachedNews.title).icontains(q),
                col(CachedNews.content).icontains(q),
            )
            conditions.append(search_condition)

        # Filter by symbol (convert to search terms)
        if symbol:
            search_terms = self._get_symbol_search_terms(symbol)
            symbol_conditions = []
            for term in search_terms:
                symbol_conditions.append(col(CachedNews.title).icontains(term))
                symbol_conditions.append(col(CachedNews.content).icontains(term))
            conditions.append(or_(*symbol_conditions))

        # Filter by source
        if source:
            conditions.append(CachedNews.source == source)

        # Filter by date range
        if from_date:
            conditions.append(CachedNews.published_at >= from_date)
        if to_date:
            conditions.append(CachedNews.published_at <= to_date)

        # Apply conditions
        for cond in conditions:
            query = query.where(cond)
            count_query = count_query.where(cond)

        # Get total count
        total = self.session.exec(count_query).one() or 0

        # Get paginated results
        query = (
            query.order_by(col(CachedNews.published_at).desc())
            .offset(offset)
            .limit(limit)
        )
        results = self.session.exec(query).all()

        # Load analysis for each news
        items = []
        for news in results:
            analysis_query = select(AnalysisResult).where(
                AnalysisResult.news_id == news.news_id
            )
            news.analysis = self.session.exec(analysis_query).first()
            items.append(self._to_news_item(news))

        return NewsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(offset + limit) < total,
        )

    async def get_news_detail(self, news_id: str) -> Optional[NewsDetailResponse]:
        """Get detailed news by ID"""
        query = select(CachedNews).where(CachedNews.news_id == news_id)
        news = self.session.exec(query).first()

        if not news:
            return None

        # Load analysis
        analysis_query = select(AnalysisResult).where(
            AnalysisResult.news_id == news.news_id
        )
        analysis_result = self.session.exec(analysis_query).first()

        analysis = None
        if analysis_result:
            analysis = NewsAnalysisResponse(
                sentiment=analysis_result.sentiment,
                confidence=analysis_result.confidence,
                trend=analysis_result.trend,
                reasoning=analysis_result.reasoning,
            )

        # Extract symbols from content (simple keyword matching)
        symbols = self._extract_symbols(news.content)

        return NewsDetailResponse(
            id=news.news_id,
            title=news.title,
            source=news.source,
            url=news.news_id,  # news_id stores the original article URL
            content=news.content,
            published_at=news.published_at,
            analysis=analysis,
            related_symbols=symbols,
        )

    async def get_news_by_symbol(
        self, symbol: str, limit: int = 10
    ) -> NewsBySymbolResponse:
        """Get news related to a specific symbol"""
        # Normalize symbol for search
        search_terms = self._get_symbol_search_terms(symbol)

        # Build OR conditions for search
        conditions = []
        for term in search_terms:
            conditions.append(col(CachedNews.title).icontains(term))
            conditions.append(col(CachedNews.content).icontains(term))

        query = (
            select(CachedNews)
            .where(or_(*conditions))
            .order_by(col(CachedNews.published_at).desc())
            .limit(limit)
        )
        results = self.session.exec(query).all()

        # Count total
        count_query = select(func.count()).select_from(CachedNews).where(or_(*conditions))
        total = self.session.exec(count_query).one() or 0

        items = []
        for news in results:
            analysis_query = select(AnalysisResult).where(
                AnalysisResult.news_id == news.news_id
            )
            news.analysis = self.session.exec(analysis_query).first()
            items.append(self._to_news_item(news))

        return NewsBySymbolResponse(symbol=symbol, items=items, total=total)

    async def search_news(
        self,
        query: str,
        source: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> Tuple[List[NewsItemResponse], int]:
        """Search news by keyword"""
        # Build search query
        search_query = select(CachedNews).where(
            or_(
                col(CachedNews.title).icontains(query),
                col(CachedNews.content).icontains(query),
            )
        )

        count_conditions = [
            or_(
                col(CachedNews.title).icontains(query),
                col(CachedNews.content).icontains(query),
            )
        ]

        if source:
            search_query = search_query.where(CachedNews.source == source)
            count_conditions.append(CachedNews.source == source)

        if from_date:
            search_query = search_query.where(CachedNews.published_at >= from_date)
            count_conditions.append(CachedNews.published_at >= from_date)

        if to_date:
            search_query = search_query.where(CachedNews.published_at <= to_date)
            count_conditions.append(CachedNews.published_at <= to_date)

        # Count total
        count_query = select(func.count()).select_from(CachedNews)
        for cond in count_conditions:
            count_query = count_query.where(cond)
        total = self.session.exec(count_query).one() or 0

        # Get results
        search_query = (
            search_query.order_by(col(CachedNews.published_at).desc()).limit(limit)
        )
        results = self.session.exec(search_query).all()

        items = []
        for news in results:
            analysis_query = select(AnalysisResult).where(
                AnalysisResult.news_id == news.news_id
            )
            news.analysis = self.session.exec(analysis_query).first()
            items.append(self._to_news_item(news))

        return items, total

    def _get_symbol_search_terms(self, symbol: str) -> List[str]:
        """Get search terms for a symbol"""
        symbol_map = {
            "BTCUSDT": ["bitcoin", "btc", "Bitcoin"],
            "ETHUSDT": ["ethereum", "eth", "Ethereum"],
            "BNBUSDT": ["binance coin", "bnb", "BNB"],
            "XRPUSDT": ["ripple", "xrp", "XRP"],
            "SOLUSDT": ["solana", "sol", "Solana"],
            "ADAUSDT": ["cardano", "ada", "Cardano"],
            "DOGEUSDT": ["dogecoin", "doge", "Dogecoin"],
            "DOTUSDT": ["polkadot", "dot", "Polkadot"],
            "MATICUSDT": ["polygon", "matic", "Polygon"],
            "LTCUSDT": ["litecoin", "ltc", "Litecoin"],
        }

        base_symbol = symbol.upper().replace("USDT", "")
        terms = symbol_map.get(symbol.upper(), [base_symbol, base_symbol.lower()])
        return terms

    def _extract_symbols(self, content: str) -> List[str]:
        """Extract cryptocurrency symbols from content"""
        symbol_keywords = {
            "bitcoin": "BTCUSDT",
            "btc": "BTCUSDT",
            "ethereum": "ETHUSDT",
            "eth": "ETHUSDT",
            "binance coin": "BNBUSDT",
            "bnb": "BNBUSDT",
            "ripple": "XRPUSDT",
            "xrp": "XRPUSDT",
            "solana": "SOLUSDT",
            "sol": "SOLUSDT",
            "cardano": "ADAUSDT",
            "ada": "ADAUSDT",
            "dogecoin": "DOGEUSDT",
            "doge": "DOGEUSDT",
            "polkadot": "DOTUSDT",
            "polygon": "MATICUSDT",
            "litecoin": "LTCUSDT",
        }

        content_lower = content.lower()
        found_symbols = set()

        for keyword, symbol in symbol_keywords.items():
            if keyword in content_lower:
                found_symbols.add(symbol)

        return list(found_symbols)
