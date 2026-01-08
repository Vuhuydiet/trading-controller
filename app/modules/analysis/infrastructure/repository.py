from sqlmodel import Session
from app.modules.analysis.domain.ports import AnalysisRepositoryPort
from app.modules.analysis.domain.entities import AnalysisResult

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