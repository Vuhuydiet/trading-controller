from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlmodel import Session, select

from .dtos import AnalysisHistoryResponse, PredictionRecord, AccuracyStats
from app.modules.analysis.domain.entities import PredictionHistory


class HistoryHandler:
    def __init__(self, session: Session):
        self.session = session

    async def get_analysis_history(
        self, symbol: str, period: str = "30d"
    ) -> AnalysisHistoryResponse:
        """Get historical predictions and accuracy for a symbol"""

        # Calculate period cutoff
        period_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "all": 365 * 10,  # Effectively all
        }
        days = period_days.get(period, 30)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get predictions from database
        statement = (
            select(PredictionHistory)
            .where(PredictionHistory.symbol == symbol)
            .where(PredictionHistory.predicted_at > cutoff)
            .order_by(PredictionHistory.predicted_at.desc())
        )
        predictions = list(self.session.exec(statement).all())

        # Calculate accuracy stats
        accuracy = self._calculate_accuracy(predictions)

        # Convert to response DTOs
        recent_predictions = [
            PredictionRecord(
                id=p.id,
                predicted_direction=p.predicted_direction,
                predicted_at=p.predicted_at,
                target_price=p.target_price,
                actual_price=p.actual_price,
                actual_direction=p.actual_direction,
                is_correct=p.is_correct,
                verified_at=p.verified_at,
            )
            for p in predictions[:20]  # Limit to 20 most recent
        ]

        return AnalysisHistoryResponse(
            symbol=symbol,
            period=period,
            accuracy=accuracy,
            recent_predictions=recent_predictions,
            generated_at=datetime.now(timezone.utc),
        )

    def _calculate_accuracy(self, predictions: List[PredictionHistory]) -> AccuracyStats:
        """Calculate accuracy statistics from predictions"""
        total = len(predictions)
        verified = [p for p in predictions if p.is_correct is not None]
        correct = [p for p in verified if p.is_correct]

        up_count = len([p for p in predictions if p.predicted_direction == "UP"])
        down_count = len([p for p in predictions if p.predicted_direction == "DOWN"])
        neutral_count = len([p for p in predictions if p.predicted_direction == "NEUTRAL"])

        accuracy_rate = len(correct) / len(verified) if verified else 0.0

        return AccuracyStats(
            total_predictions=total,
            verified_predictions=len(verified),
            correct_predictions=len(correct),
            accuracy_rate=round(accuracy_rate, 2),
            up_predictions=up_count,
            down_predictions=down_count,
            neutral_predictions=neutral_count,
        )
