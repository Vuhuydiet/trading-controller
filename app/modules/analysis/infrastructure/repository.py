from sqlmodel import Session
from app.modules.analysis.domain.ports import AnalysisRepositoryPort
from app.modules.analysis.domain.entities import AnalysisResult

class SqlModelAnalysisRepo(AnalysisRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    # Implement hàm save_analysis_result từ Port
    async def save_analysis_result(self, news_id: str, sentiment: str, confidence: float, reasoning: str) -> bool:
        try:
            # Tạo object SQLModel
            record = AnalysisResult(
                news_id=news_id,
                sentiment=sentiment,
                confidence=confidence,
                reasoning=reasoning
            )
            # Add và Commit
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return True
        except Exception as e:
            print(f"Lỗi DB: {e}")
            return False