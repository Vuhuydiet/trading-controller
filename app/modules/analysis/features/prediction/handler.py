import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select

from .dtos import (
    SymbolPredictionResponse,
    MultiPredictionResponse,
    MultiPredictionItem,
    PredictionData,
    TargetPrice,
)
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort
from app.modules.analysis.domain.entities import TrendPrediction, PredictionHistory
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient


MODEL_VERSION = "v1.0.0"


class PredictionHandler:
    def __init__(
        self,
        sentiment_analyzer: SentimentAnalyzerPort,
        reasoner: MarketReasonerPort,
        session: Session,
    ):
        self.sentiment_analyzer = sentiment_analyzer
        self.reasoner = reasoner
        self.session = session
        self.binance_client = BinanceRestClient()

    async def get_symbol_prediction(
        self, symbol: str, timeframe: str = "24h"
    ) -> SymbolPredictionResponse:
        """Get AI price trend prediction for a symbol"""

        # Get current price from Binance
        current_price = await self._get_current_price(symbol)

        # Create analysis context
        analysis_context = f"""
        Analyze the price trend for {symbol} over the next {timeframe}.
        Current price: {current_price}
        Consider technical indicators, market sentiment, and recent news.
        """

        # Get AI predictions
        sentiment_result = await self.sentiment_analyzer.analyze_sentiment(
            f"Market outlook for {symbol}"
        )
        reasoning_result = await self.reasoner.explain_market_trend(
            news=analysis_context,
            price_change=0
        )

        # Calculate prediction based on AI output
        direction = reasoning_result.trend
        confidence = sentiment_result.score

        # Calculate target prices based on direction and confidence
        price_float = float(current_price)
        targets = self._calculate_targets(price_float, direction, confidence, timeframe)
        support_levels, resistance_levels = self._calculate_levels(price_float, direction)

        # Save prediction to database
        db_prediction = TrendPrediction(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            direction=direction,
            confidence=confidence,
            target_low=targets.low,
            target_mid=targets.mid,
            target_high=targets.high,
            support_levels=json.dumps(support_levels),
            resistance_levels=json.dumps(resistance_levels),
            model_version=MODEL_VERSION,
        )
        self.session.add(db_prediction)

        # Save to prediction history for accuracy tracking
        history = PredictionHistory(
            symbol=symbol,
            predicted_direction=direction,
            predicted_at=datetime.now(timezone.utc),
            target_price=targets.mid,
        )
        self.session.add(history)
        self.session.commit()

        return SymbolPredictionResponse(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            prediction=PredictionData(
                direction=direction,
                confidence=round(confidence, 2),
                target_price=targets,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
            ),
            model_version=MODEL_VERSION,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_multi_predictions(
        self, symbols: List[str], timeframe: str = "24h"
    ) -> MultiPredictionResponse:
        """Get predictions for multiple symbols"""

        predictions = []
        for symbol in symbols:
            try:
                pred = await self.get_symbol_prediction(symbol, timeframe)
                predictions.append(
                    MultiPredictionItem(
                        symbol=pred.symbol,
                        direction=pred.prediction.direction,
                        confidence=pred.prediction.confidence,
                        target_mid=pred.prediction.target_price.mid,
                        current_price=pred.current_price,
                    )
                )
            except Exception as e:
                print(f"Error getting prediction for {symbol}: {e}")
                continue

        return MultiPredictionResponse(
            timeframe=timeframe,
            predictions=predictions,
            model_version=MODEL_VERSION,
            generated_at=datetime.now(timezone.utc),
        )

    async def _get_current_price(self, symbol: str) -> str:
        """Get current price from Binance"""
        try:
            ticker = await self.binance_client.get_ticker_24hr(symbol)
            if isinstance(ticker, dict):
                return ticker.get("lastPrice", "0.00")
            return "0.00"
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return "0.00"

    def _calculate_targets(
        self, current_price: float, direction: str, confidence: float, timeframe: str
    ) -> TargetPrice:
        """Calculate target prices based on prediction"""

        # Timeframe multipliers
        timeframe_mult = {
            "1h": 0.01,
            "4h": 0.02,
            "24h": 0.05,
            "7d": 0.15,
        }
        base_mult = timeframe_mult.get(timeframe, 0.05)

        # Direction determines sign
        if direction == "UP":
            sign = 1
        elif direction == "DOWN":
            sign = -1
        else:
            sign = 0

        # Calculate targets
        change_pct = base_mult * confidence * sign

        if sign == 0:
            # Neutral - small range
            low = current_price * 0.98
            mid = current_price
            high = current_price * 1.02
        else:
            mid = current_price * (1 + change_pct)
            low = current_price * (1 + change_pct * 0.5)
            high = current_price * (1 + change_pct * 1.5)

        return TargetPrice(
            low=f"{low:.2f}",
            mid=f"{mid:.2f}",
            high=f"{high:.2f}",
        )

    def _calculate_levels(
        self, current_price: float, direction: str
    ) -> tuple[List[str], List[str]]:
        """Calculate support and resistance levels"""

        # Simple percentage-based levels
        support_pcts = [0.97, 0.94, 0.90]
        resistance_pcts = [1.03, 1.06, 1.10]

        support_levels = [f"{current_price * pct:.2f}" for pct in support_pcts]
        resistance_levels = [f"{current_price * pct:.2f}" for pct in resistance_pcts]

        return support_levels, resistance_levels
