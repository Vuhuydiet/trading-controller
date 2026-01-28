from typing import List
from sqlmodel import Session, select, col
from datetime import datetime, timezone
from app.modules.analysis.domain.ports import AnalysisRepositoryPort
from app.modules.analysis.domain.entities import AnalysisResult
from app.modules.analysis.domain.entities import CachedNews
from sqlalchemy.orm import joinedload
from sqlmodel import select, func


class SqlModelAnalysisRepo(AnalysisRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    async def save_analysis_result(
        self, 
        news_id: str, 
        sentiment: str, 
        confidence: float, 
        trend: str,
        reasoning: str
    ) -> bool:
        try:
            record = AnalysisResult(
                news_id=news_id,
                sentiment=sentiment,
                confidence=confidence,
                trend=trend,
                reasoning=reasoning
            )
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return True
        except Exception as e:
            print(f"Lỗi DB: {e}")
            return False
        
    # 1. Hàm lưu tin tức (Gọi khi Consumer nhận tin)
    async def cache_news(self, news_data: dict) -> bool:
        try:
            # Kiểm tra trùng lặp
            statement = select(CachedNews).where(CachedNews.news_id == news_data['url'])
            existing = self.session.exec(statement).first()
            
            if not existing:
                published_date = news_data.get('published_date')
                if not published_date:
                    published_date = datetime.now(timezone.utc)
                news = CachedNews(
                    news_id=news_data['url'],
                    title=news_data['title'],
                    source=news_data.get('source', 'unknown'),
                    content=news_data.get('content', ''),
                    published_at=published_date
                )
                self.session.add(news)
                self.session.commit()
            return True
        except Exception as e:
            print(f"Lỗi cache news: {e}")
            return False

    # 2. Hàm lấy tin tức cho Chatbot (Thay thế Mongo)
    async def get_recent_news(self, symbol: str, limit: int = 3) -> List[CachedNews]:
            statement = (
                select(CachedNews)
                .where(
                    (col(CachedNews.title).contains(symbol)) | 
                    (col(CachedNews.content).contains(symbol))
                )
                .order_by(col(CachedNews.published_at).desc())
                .limit(limit)
            )
            results = self.session.exec(statement).all()
            return list(results) if results else []
    
    async def get_news_feed_with_count(self, limit: int = 20, offset: int = 0) -> tuple[List[CachedNews], int]:
        """
        Lấy danh sách News KÈM THEO kết quả Analysis + total count trong 1 query
        """
        # Get total count first (fast with index on published_at)
        count_stmt = select(func.count()).select_from(CachedNews)
        total = self.session.exec(count_stmt).one() or 0

        # Get paginated data with analysis
        statement = (
            select(CachedNews)
            .options(joinedload(CachedNews.analysis)) # type: ignore
            .order_by(col(CachedNews.published_at).desc())
            .offset(offset)
            .limit(limit)
        )
        results = self.session.exec(statement).unique().all()
        return (list(results) if results else [], total)

    async def get_news_feed(self, limit: int = 20, offset: int = 0) -> List[CachedNews]:
        """
        Lấy danh sách News KÈM THEO kết quả Analysis
        """
        statement = (
            select(CachedNews)
            .options(joinedload(CachedNews.analysis)) # type: ignore
            .order_by(col(CachedNews.published_at).desc())
            .offset(offset)
            .limit(limit)
        )
        results = self.session.exec(statement).unique().all()
        return list(results) if results else []

    async def count_news(self) -> int:
        statement = select(func.count()).select_from(CachedNews)
        return self.session.exec(statement).one() or 0

    async def get_news_without_analysis(self, limit: int = 10) -> List[CachedNews]:
        """Get news that don't have analysis yet"""
        statement = (
            select(CachedNews)
            .outerjoin(AnalysisResult, CachedNews.news_id == AnalysisResult.news_id)
            .where(AnalysisResult.id == None)
            .order_by(col(CachedNews.published_at).desc())
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return list(results) if results else []