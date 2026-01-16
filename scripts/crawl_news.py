#!/usr/bin/env python3
"""
News Crawler Script - Standalone entry point for periodic news crawling.

This script crawls news from various sources (CoinDesk, Reuters, Bloomberg, Twitter),
processes them with LLM to generate insights, and publishes to Kafka message queue.

Usage:
    python scripts/crawl_news.py [--once]

Options:
    --once      Run once and exit (default: run periodically)
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.modules.news.domain.article import NewsSource
from app.modules.news.domain.kafka_service import NewsKafkaService
from app.modules.news.infrastructure.crawlers import (
    BloombergCrawler,
    CoinDeskCrawler,
    ReutersCrawler,
    TwitterCrawler,
)
from app.modules.news.infrastructure.kafka_producer import KafkaNewsProducer
from app.modules.news.infrastructure.llm_adapter import get_llm_adapter
from app.shared.core.config import settings
from app.shared.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Global state
kafka_producer: KafkaNewsProducer | None = None
news_service: NewsKafkaService | None = None
scheduler: AsyncIOScheduler | None = None


async def initialize_services():
    """Initialize Kafka producer and news service"""
    global kafka_producer, news_service

    logger.info("Initializing news crawler services...")

    # Initialize Kafka producer
    kafka_producer = KafkaNewsProducer()
    kafka_producer.start()

    # Initialize crawlers based on configured sources
    crawlers = {}
    for source_name in settings.NEWS_SOURCES:
        try:
            source = NewsSource(source_name.lower())
            if source == NewsSource.COINDESK:
                crawlers[source] = CoinDeskCrawler()
            elif source == NewsSource.REUTERS:
                crawlers[source] = ReutersCrawler()
            elif source == NewsSource.BLOOMBERG:
                crawlers[source] = BloombergCrawler()
            elif source == NewsSource.TWITTER:
                crawlers[source] = TwitterCrawler()
            logger.info(f"Initialized crawler for {source.value}")
        except ValueError:
            logger.warning(f"Unknown news source: {source_name}")

    # Initialize LLM adapter
    llm_adapter = get_llm_adapter()

    # Create news service
    news_service = NewsKafkaService(
        kafka_producer=kafka_producer,
        crawlers=crawlers,
        llm_adapter=llm_adapter,
    )

    logger.info("All services initialized successfully")


async def cleanup_services():
    """Cleanup and shutdown services"""
    global kafka_producer, scheduler

    logger.info("Shutting down services...")

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    if kafka_producer:
        kafka_producer.stop()
        logger.info("Kafka producer stopped")


async def crawl_job():
    """Execute the news crawling job"""
    global news_service

    logger.info(f"Starting news crawl at {datetime.now(timezone.utc)}")

    if not news_service:
        logger.error("News service not initialized")
        return

    try:
        results = await news_service.crawl_and_publish_news()
        logger.info(
            f"Crawl completed - Articles: {results['published_articles']}, "
            f"Insights: {results['published_insights']}, "
            f"Duplicates: {results['duplicates']}, "
            f"Failed: {results['failed']}"
        )
        if results["errors"]:
            logger.warning(f"Errors during crawl: {results['errors']}")
    except Exception as e:
        logger.error(f"Fatal error in crawl job: {str(e)}", exc_info=True)


async def run_once():
    """Run the crawler once and exit"""
    try:
        await initialize_services()
        await crawl_job()
    finally:
        await cleanup_services()


async def run_periodic():
    """Run the crawler periodically using scheduler"""
    global scheduler

    try:
        await initialize_services()

        # Setup scheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            crawl_job,
            trigger=IntervalTrigger(minutes=settings.NEWS_CRAWL_INTERVAL_MINUTES),
            id="news_crawl_job",
            name="News Crawling Job",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(
            f"News crawler started. Running every {settings.NEWS_CRAWL_INTERVAL_MINUTES} minutes"
        )
        logger.info(
            f"Kafka topics - Articles: {settings.KAFKA_NEWS_ARTICLES_TOPIC}, "
            f"Insights: {settings.KAFKA_NEWS_INSIGHTS_TOPIC}"
        )

        # Run initial crawl
        await crawl_job()

        # Keep the script running
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Received shutdown signal")

    finally:
        await cleanup_services()


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    # Check command line arguments
    run_once_mode = "--once" in sys.argv

    logger.info("=" * 80)
    logger.info("NEWS CRAWLER SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Mode: {'ONE-TIME' if run_once_mode else 'PERIODIC'}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"News Sources: {', '.join(settings.NEWS_SOURCES)}")
    logger.info(f"Kafka Servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    logger.info("=" * 80)

    # Run in appropriate mode
    try:
        if run_once_mode:
            asyncio.run(run_once())
            logger.info("One-time crawl completed successfully")
        else:
            asyncio.run(run_periodic())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
