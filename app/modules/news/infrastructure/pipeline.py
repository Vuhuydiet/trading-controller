import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.modules.news.domain.services import NewsService
from app.shared.core.config import settings

logger = logging.getLogger(__name__)


class NewsPipeline:
    """Manages the news crawling and processing pipeline"""

    _instance = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _news_service: Optional[NewsService] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls, news_service: NewsService):
        """Initialize the pipeline with dependencies"""
        cls._news_service = news_service
        cls._scheduler = AsyncIOScheduler()
        logger.info("News pipeline initialized")

    @classmethod
    async def start(cls):
        """Start the news crawling pipeline"""
        if not cls._scheduler:
            logger.error("Pipeline not initialized. Call initialize() first.")
            return

        if cls._scheduler.running:
            logger.warning("Pipeline already running")
            return

        # Schedule the crawl job
        cls._scheduler.add_job(
            cls._crawl_and_process_job,
            trigger=IntervalTrigger(minutes=settings.NEWS_CRAWL_INTERVAL_MINUTES),
            id="news_crawl_job",
            name="News Crawling and Processing Job",
            replace_existing=True,
        )

        cls._scheduler.start()
        logger.info(
            f"News pipeline started. Will crawl every {settings.NEWS_CRAWL_INTERVAL_MINUTES} minutes"
        )

        # Run initial crawl
        await cls._crawl_and_process_job()

    @classmethod
    async def stop(cls):
        """Stop the news crawling pipeline"""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("News pipeline stopped")

    @classmethod
    async def _crawl_and_process_job(cls):
        """The actual job that crawls and processes news"""
        logger.info(f"Starting news crawl at {datetime.now(timezone.utc)}")
        try:
            if cls._news_service:
                results = await cls._news_service.crawl_and_process_news()
                logger.info(f"News crawl completed: {results}")
            else:
                logger.error("NewsService not initialized")
        except Exception as e:
            logger.error(f"Error in news crawl job: {str(e)}", exc_info=True)

    @classmethod
    async def trigger_manual_crawl(cls):
        """Manually trigger a news crawl"""
        logger.info("Manual news crawl triggered")
        await cls._crawl_and_process_job()

    @classmethod
    def get_scheduler(cls) -> Optional[AsyncIOScheduler]:
        """Get the scheduler instance"""
        return cls._scheduler
