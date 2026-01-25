import json
import asyncio
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from sqlmodel import Session
from datetime import datetime 

# 👇 1. SỬA IMPORT: Lấy hàm get_logger thay vì biến logger
from app.shared.core.logging_config import get_logger
from app.shared.core.config import settings
from app.shared.infrastructure.db import engine

# Import Handler và DTO
from app.modules.analysis.features.analyze_news.handler import AnalyzeNewsHandler
from app.modules.analysis.features.analyze_news.dtos import AnalyzeNewsRequest

# Import Dependencies
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo
from app.shared.infrastructure.ai.sentiment_adapter import FinBertAdapter
from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
from app.modules.analysis.domain.services import NewsPriceAligner

logger = get_logger("analysis_consumer")

class AnalysisConsumer:
    def __init__(self):
        self.topic = settings.KAFKA_NEWS_ARTICLES_TOPIC
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.loop = asyncio.get_event_loop()

    async def start(self):
        """Hàm này sẽ chạy ngầm vĩnh viễn"""
        logger.info("Pre-loading AI Models...")
        finbert_bot = FinBertAdapter() 
        ollama_bot = OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL)
        logger.info("AI Models Ready!")

        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="analysis_group",
            # Deserializer trả về Dict hoặc None nếu lỗi
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else {}
        )

        try:
            await consumer.start()
            logger.info(f"Analysis Consumer started listening on topic: {self.topic}")
            
            async for msg in consumer:
                try:
                    payload: Dict[str, Any] = msg.value # type: ignore
                    
                    if not payload or not isinstance(payload, dict):
                        logger.warning("Received invalid or empty payload")
                        continue

                    logger.info(f"Received news payload: {payload.get('url', 'No ID')}")
                    
                    with Session(engine) as session:
                        handler = AnalyzeNewsHandler(
                            sentiment_bot=finbert_bot,
                            reasoning_bot=ollama_bot,
                            repo=SqlModelAnalysisRepo(session),
                            aligner=NewsPriceAligner()
                        )
                        
                        news_content = payload.get("content") or payload.get("title") or ""
                        
                        if not news_content:
                            logger.warning("Skipping news with empty content")
                            continue

                        raw_published_at = payload.get("published_at")
                        final_published_at = raw_published_at if raw_published_at else datetime.now()

                        request = AnalyzeNewsRequest(
                            news_id=str(payload.get("url", "unknown_id")), 
                            news_content=str(news_content),
                            published_at=final_published_at # type: ignore
                        )
                        await handler.execute(request)
                        logger.info(f"AI Analysis completed for: {request.news_id}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Kafka Connection Failed: {e}")
        finally:
            await consumer.stop()

def start_analysis_consumer():
    consumer = AnalysisConsumer()
    asyncio.create_task(consumer.start())