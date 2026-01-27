#!/usr/bin/env python3
"""Quick test to verify crawler fixes"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.news.infrastructure.crawlers import CoinDeskCrawler, BloombergCrawler

async def main():
    print("=" * 60)
    print("Testing CoinDesk Crawler (with Google News fallback)")
    print("=" * 60)

    coindesk = CoinDeskCrawler()
    articles = await coindesk.fetch_news()

    print(f"Found {len(articles)} articles from CoinDesk")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n  [{i}] {article.title[:60]}...")
        print(f"      URL: {article.url[:50]}...")
        print(f"      Content: {len(article.content)} chars")

    print("\n" + "=" * 60)
    print("Testing Bloomberg Crawler (Google News RSS)")
    print("=" * 60)

    bloomberg = BloombergCrawler()
    articles = await bloomberg.fetch_news()

    print(f"Found {len(articles)} articles from Bloomberg")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n  [{i}] {article.title[:60]}...")
        print(f"      URL: {article.url[:50]}...")
        print(f"      Content: {len(article.content)} chars")

if __name__ == "__main__":
    asyncio.run(main())
