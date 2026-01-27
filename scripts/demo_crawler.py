#!/usr/bin/env python3
"""
Demo Crawler Script - For presentation/demo purposes.

This script demonstrates the adaptive HTML crawler without requiring Kafka.
It crawls news, shows the adaptive parsing in action, and saves directly to database.

Usage:
    python scripts/demo_crawler.py
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.shared.core.logging_config import setup_logging
setup_logging()

import logging
from sqlmodel import Session

from app.modules.news.domain.article import NewsSource
from app.modules.news.infrastructure.crawlers import (
    CoinDeskCrawler,
    ReutersCrawler,
    BloombergCrawler,
    AdaptiveCrawlerMixin,
)
from app.modules.news.infrastructure.structure_learner import (
    StructureLearner,
    get_structure_learner,
)
from app.modules.analysis.domain.entities import CachedNews
from app.shared.infrastructure.db import engine, create_db_and_tables

logger = logging.getLogger(__name__)


def print_banner():
    print("=" * 70)
    print("   ADAPTIVE NEWS CRAWLER DEMO")
    print("   Auto-Learning HTML Structure")
    print("=" * 70)
    print()


def print_article(article, index, method="unknown", confidence=0.0):
    """Pretty print an article"""
    print(f"\n{'─' * 60}")
    print(f"📰 Article #{index}")
    print(f"{'─' * 60}")
    print(f"   Source:      {article.source}")
    print(f"   Title:       {article.title[:60]}...")
    print(f"   URL:         {article.url[:50]}...")
    print(f"   Published:   {article.published_at}")
    print(f"   Content:     {len(article.content)} chars")
    print(f"   Extraction:  {method} (confidence: {confidence:.2f})")


async def demo_single_crawler(crawler_class, source_name: str, session: Session):
    """Demo a single crawler"""
    print(f"\n{'=' * 60}")
    print(f"🔍 Testing {source_name} Crawler (Adaptive Mode)")
    print(f"{'=' * 60}")

    crawler = crawler_class()

    try:
        print(f"\n⏳ Fetching news from {source_name}...")
        articles = await crawler.fetch_news()

        if not articles:
            print(f"❌ No articles found from {source_name}")
            return 0

        print(f"✅ Found {len(articles)} articles!")

        # Show first 3 articles
        for i, article in enumerate(articles[:3], 1):
            # Get extraction info from parser if available
            parser = AdaptiveCrawlerMixin.get_parser()
            domain = article.url.split("/")[2] if "/" in article.url else "unknown"
            patterns = parser.learned_patterns.get(domain, {})
            confidence = patterns.get("confidence", 0.5)
            method = patterns.get("extraction_method", "adaptive")

            print_article(article, i, method, confidence)

            # Save to database
            try:
                existing = session.query(CachedNews).filter(
                    CachedNews.news_id == article.url
                ).first()

                if not existing:
                    cached = CachedNews(
                        news_id=article.url,
                        title=article.title,
                        source=article.source,
                        content=article.content[:2000],  # Limit content
                        published_at=article.published_at,
                    )
                    session.add(cached)
                    session.commit()
                    print(f"   💾 Saved to database")
                else:
                    print(f"   ℹ️  Already in database")
            except Exception as e:
                print(f"   ⚠️  DB save error: {e}")

        return len(articles)

    except Exception as e:
        print(f"❌ Error crawling {source_name}: {e}")
        logger.exception(f"Crawler error for {source_name}")
        return 0


async def show_learned_patterns(session: Session):
    """Show learned HTML patterns"""
    print(f"\n{'=' * 60}")
    print("🧠 LEARNED HTML PATTERNS")
    print(f"{'=' * 60}")

    learner = get_structure_learner(session)
    patterns = learner.get_all_patterns()

    if not patterns:
        print("   No patterns learned yet.")
        print("   (Patterns are learned after successful extractions)")
    else:
        for domain, pattern in patterns.items():
            print(f"\n   📌 Domain: {domain}")
            print(f"      Content selectors: {pattern.get('content_selectors', [])}")
            print(f"      Confidence: {pattern.get('confidence', 0):.2f}")
            print(f"      Version: {pattern.get('version', 1)}")


async def main():
    print_banner()

    # Initialize database
    print("📦 Initializing database...")
    create_db_and_tables()
    print("✅ Database ready!\n")

    total_articles = 0

    with Session(engine) as session:
        # Demo each crawler
        crawlers = [
            (CoinDeskCrawler, "CoinDesk"),
            # (ReutersCrawler, "Reuters"),  # Often blocked
            # (BloombergCrawler, "Bloomberg"),  # Often blocked
        ]

        for crawler_class, name in crawlers:
            count = await demo_single_crawler(crawler_class, name, session)
            total_articles += count
            await asyncio.sleep(1)  # Be nice to servers

        # Show learned patterns
        await show_learned_patterns(session)

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 DEMO SUMMARY")
    print(f"{'=' * 60}")
    print(f"   Total articles crawled: {total_articles}")
    print(f"   Articles saved to DB:   Check /api/v1/news endpoint")
    print(f"\n💡 To view crawled news:")
    print(f"   1. Run: .\\start_local.bat")
    print(f"   2. Open: http://localhost:8000/docs")
    print(f"   3. Try:  GET /api/v1/news")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        logger.exception("Demo failed")
