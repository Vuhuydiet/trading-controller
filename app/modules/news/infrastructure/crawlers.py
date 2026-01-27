"""
News Crawlers with Adaptive HTML Parsing

This module provides crawlers for multiple news sources with:
1. Adaptive HTML structure learning
2. Fallback extraction strategies
3. Pattern persistence and reuse
4. Rate limiting to avoid being blocked
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.modules.news.domain.article import ArticleStatus, NewsArticle, NewsSource
from app.modules.news.domain.ports import NewsCrawler
from app.modules.news.infrastructure.adaptive_parser import (
    AdaptiveHTMLParser,
    ExtractedContent,
    get_adaptive_parser,
)

logger = logging.getLogger(__name__)


# Rate limiting configuration
RATE_LIMIT_DELAY = 2.0  # Base delay between requests (seconds)
RATE_LIMIT_JITTER = 1.0  # Random jitter added to delay (0 to this value)


async def rate_limited_delay():
    """Add a random delay between requests to avoid rate limiting"""
    delay = RATE_LIMIT_DELAY + random.uniform(0, RATE_LIMIT_JITTER)
    await asyncio.sleep(delay)


class AdaptiveCrawlerMixin:
    """
    Mixin that adds adaptive parsing capabilities to crawlers.
    """

    _shared_parser: Optional[AdaptiveHTMLParser] = None
    _learned_patterns: Dict[str, Any] = {}

    @classmethod
    def get_parser(cls) -> AdaptiveHTMLParser:
        """Get shared adaptive parser instance"""
        if cls._shared_parser is None:
            cls._shared_parser = get_adaptive_parser(cls._learned_patterns)
        return cls._shared_parser

    @classmethod
    def load_patterns(cls, patterns: Dict[str, Any]):
        """Load patterns from database into parser"""
        cls._learned_patterns = patterns
        cls._shared_parser = None  # Force recreation

    async def parse_with_adaptive(
        self,
        html: str,
        url: str,
        source: NewsSource,
        min_confidence: float = 0.3,
    ) -> Optional[NewsArticle]:
        """
        Parse HTML using adaptive parser with fallback strategies.
        """
        parser = self.get_parser()

        try:
            extracted = parser.parse(html, url)

            if extracted.confidence < min_confidence:
                logger.warning(
                    f"Low confidence extraction ({extracted.confidence:.2f}) for {url}"
                )
                return None

            # Create article from extracted content
            article = NewsArticle(
                source=source,
                title=extracted.title,
                content=extracted.content,
                url=url,
                author=extracted.author,
                published_at=extracted.published_at or datetime.now(timezone.utc),
                status=ArticleStatus.CRAWLED,
            )

            # Learn from successful extraction
            if extracted.confidence > 0.6:
                pattern = parser.learn_from_success(url, extracted)
                if pattern:
                    logger.debug(f"Learned pattern for {urlparse(url).netloc}")

            return article

        except Exception as e:
            logger.error(f"Adaptive parsing failed for {url}: {e}")
            return None


class CoinDeskCrawler(NewsCrawler, AdaptiveCrawlerMixin):
    """Crawler for CoinDesk news with adaptive parsing"""

    BASE_URL = "https://www.coindesk.com"
    FEED_URL = "https://www.coindesk.com/feed"
    # Fallback: Use Google News RSS for CoinDesk articles
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q=cryptocurrency+OR+bitcoin+site:coindesk.com&hl=en-US&gl=US&ceid=US:en"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from CoinDesk"""
        import feedparser

        articles: List[NewsArticle] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try direct RSS feed first
                response = await client.get(self.FEED_URL)
                if response.status_code == 200:
                    parsed = await self._parse_rss_feed(response.text, NewsSource.COINDESK)
                    articles.extend(parsed)

                # If direct feed failed or returned no articles, try Google News RSS
                if not articles:
                    logger.info("CoinDesk direct feed empty, trying Google News RSS fallback")
                    response = await client.get(
                        self.GOOGLE_NEWS_RSS,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    )
                    if response.status_code == 200:
                        feed = feedparser.parse(response.text)
                        for entry in feed.entries[:10]:
                            try:
                                url = entry.link
                                title = entry.title

                                # Clean up title
                                if " - CoinDesk" in title:
                                    title = title.replace(" - CoinDesk", "").strip()

                                # Parse publication date
                                published = datetime.now(timezone.utc)
                                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                                # Get summary/content
                                content = ""
                                if hasattr(entry, 'summary'):
                                    soup = BeautifulSoup(entry.summary, "html.parser")
                                    content = soup.get_text(strip=True)

                                article = NewsArticle(
                                    source=NewsSource.COINDESK,
                                    title=title,
                                    content=content or title,
                                    url=url,
                                    author=None,
                                    published_at=published,
                                    status=ArticleStatus.CRAWLED,
                                )
                                articles.append(article)
                                logger.info(f"Found CoinDesk article: {title[:50]}...")
                            except Exception as e:
                                logger.warning(f"Error parsing Google News entry: {e}")
                                continue

                # Try to get full articles for better content (limit to avoid rate limiting)
                for article in articles[:3]:
                    try:
                        await rate_limited_delay()
                        full_article = await self.parse_article(article.url)
                        if full_article and len(full_article.content) > len(article.content):
                            article.content = full_article.content
                    except Exception:
                        pass  # Keep RSS content if full parse fails

        except Exception as e:
            logger.error(f"Error fetching CoinDesk news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single CoinDesk article using adaptive parser"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"},
                )
                response.raise_for_status()

                # Use adaptive parser
                return await self.parse_with_adaptive(
                    response.text, url, NewsSource.COINDESK
                )

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error parsing CoinDesk article {url}: {str(e)}")
            return None

    async def _parse_rss_feed(
        self, feed_content: str, source: NewsSource
    ) -> List[NewsArticle]:
        """Parse RSS feed content"""
        import feedparser

        articles: List[NewsArticle] = []
        feed_result: dict[str, Any] = {}

        try:
            feed_result = feedparser.parse(feed_content)

            # Check for feed errors
            if feed_result.get("bozo"):
                logger.warning(
                    f"RSS Feed warning: {feed_result.get('bozo_exception')}"
                )

            entries: list[Any] = feed_result.get("entries") or []

            for entry in entries[:10]:  # Get latest 10
                try:
                    entry_dict: dict[str, Any] = entry

                    # Parse published date
                    published_at = datetime.now(timezone.utc)
                    if entry_dict.get("published_parsed"):
                        try:
                            published_at = datetime.fromtimestamp(
                                time.mktime(entry_dict["published_parsed"]),
                                tz=timezone.utc,
                            )
                        except Exception:
                            pass

                    article = NewsArticle(
                        source=source,
                        title=str(entry_dict.get("title", "")).strip(),
                        content=self._clean_html_content(
                            str(entry_dict.get("summary", ""))
                        ),
                        url=str(entry_dict.get("link", "")),
                        author=str(entry_dict.get("author", "")) or None,
                        published_at=published_at,
                        status=ArticleStatus.CRAWLED,
                    )

                    if article.title and article.url:
                        articles.append(article)

                except Exception as e:
                    logger.debug(f"Error parsing RSS entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing RSS feed: {str(e)}")

        return articles

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content from RSS feed"""
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)


class ReutersCrawler(NewsCrawler, AdaptiveCrawlerMixin):
    """Crawler for Reuters cryptocurrency news with adaptive parsing"""

    BASE_URL = "https://www.reuters.com"
    CRYPTO_URL = "https://www.reuters.com/technology/cryptocurrency/"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from Reuters"""
        articles: List[NewsArticle] = []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    self.CRYPTO_URL,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )

                if response.status_code != 200:
                    logger.warning(f"Reuters returned status {response.status_code}")
                    return articles

                soup = BeautifulSoup(response.text, "html.parser")

                # Find article links - Reuters uses various patterns
                article_links = set()

                # Pattern 1: Links with /technology/ or /markets/ in href
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if isinstance(href, str) and any(
                        pattern in href
                        for pattern in ["/technology/", "/markets/", "/business/"]
                    ):
                        if href.startswith("/"):
                            href = self.BASE_URL + href
                        if "cryptocurrency" in href or "bitcoin" in href.lower():
                            article_links.add(href)

                # Parse top articles
                for link in list(article_links)[:10]:
                    article = await self.parse_article(link)
                    if article:
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Reuters news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single Reuters article using adaptive parser"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                response.raise_for_status()

                return await self.parse_with_adaptive(
                    response.text, url, NewsSource.REUTERS
                )

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Reuters article {url}: {str(e)}")
            return None


class BloombergCrawler(NewsCrawler, AdaptiveCrawlerMixin):
    """Crawler for Bloomberg cryptocurrency news using Google News RSS"""

    BASE_URL = "https://www.bloomberg.com"
    # Use Google News RSS as reliable fallback
    RSS_URL = "https://news.google.com/rss/search?q=cryptocurrency+OR+bitcoin+site:bloomberg.com&hl=en-US&gl=US&ceid=US:en"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from Bloomberg via Google News RSS"""
        import feedparser

        articles: List[NewsArticle] = []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    self.RSS_URL,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )

                if response.status_code != 200:
                    logger.warning(f"Google News RSS returned status {response.status_code}")
                    return articles

                feed = feedparser.parse(response.text)

                for entry in feed.entries[:10]:
                    try:
                        # Google News RSS already filters by site:bloomberg.com
                        # The entry.link is a Google redirect URL, not direct Bloomberg URL
                        # We accept all entries since the query already filters for Bloomberg
                        url = entry.link
                        title = entry.title

                        # Clean up title (remove " - Bloomberg" suffix if present)
                        if " - Bloomberg" in title:
                            title = title.replace(" - Bloomberg", "").strip()
                        elif " - Bloomberg.com" in title:
                            title = title.replace(" - Bloomberg.com", "").strip()

                        # Parse publication date
                        published = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                        # Get summary/content
                        content = ""
                        if hasattr(entry, 'summary'):
                            soup = BeautifulSoup(entry.summary, "html.parser")
                            content = soup.get_text(strip=True)

                        article = NewsArticle(
                            source=NewsSource.BLOOMBERG,
                            title=title,
                            content=content or title,
                            url=url,
                            author=None,
                            published_at=published,
                            status=ArticleStatus.CRAWLED,
                        )
                        articles.append(article)
                        logger.info(f"Found Bloomberg article: {title[:50]}...")

                    except Exception as e:
                        logger.warning(f"Error parsing RSS entry: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error fetching Bloomberg news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single Bloomberg article using adaptive parser"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                response.raise_for_status()

                return await self.parse_with_adaptive(
                    response.text, url, NewsSource.BLOOMBERG
                )

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Bloomberg article {url}: {str(e)}")
            return None


class TwitterCrawler(NewsCrawler):
    """Crawler for cryptocurrency-related tweets (API-based, no HTML parsing needed)"""

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch crypto tweets from Twitter"""
        articles: List[NewsArticle] = []
        try:
            import tweepy

            from app.shared.core.config import settings

            if not settings.TWITTER_BEARER_TOKEN:
                logger.warning("Twitter API key not configured, skipping Twitter crawl")
                return articles

            client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)

            # Search for crypto-related tweets
            query = "cryptocurrency OR bitcoin OR ethereum -is:retweet lang:en"
            tweets = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["created_at", "author_id", "public_metrics"],
            )

            if tweets and tweets.data:
                for tweet in tweets.data:
                    article = NewsArticle(
                        source=NewsSource.TWITTER,
                        title=f"Tweet by @{tweet.author_id}",
                        content=tweet.text,
                        url=f"https://twitter.com/i/web/status/{tweet.id}",
                        published_at=tweet.created_at or datetime.now(timezone.utc),
                        status=ArticleStatus.CRAWLED,
                    )
                    articles.append(article)

        except ImportError:
            logger.warning("tweepy not installed, skipping Twitter crawl")
        except Exception as e:
            logger.error(f"Error fetching Twitter news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single tweet - handled during fetch"""
        return None


# Factory function to create crawlers with loaded patterns
def create_crawlers_with_patterns(
    patterns: Optional[Dict[str, Any]] = None
) -> Dict[NewsSource, NewsCrawler]:
    """
    Create crawler instances with pre-loaded patterns.

    Args:
        patterns: Dictionary of domain -> pattern data from database

    Returns:
        Dictionary mapping NewsSource to crawler instance
    """
    if patterns:
        AdaptiveCrawlerMixin.load_patterns(patterns)

    return {
        NewsSource.COINDESK: CoinDeskCrawler(),
        NewsSource.REUTERS: ReutersCrawler(),
        NewsSource.BLOOMBERG: BloombergCrawler(),
        NewsSource.TWITTER: TwitterCrawler(),
    }


# Backward compatible exports
__all__ = [
    "CoinDeskCrawler",
    "ReutersCrawler",
    "BloombergCrawler",
    "TwitterCrawler",
    "AdaptiveCrawlerMixin",
    "create_crawlers_with_patterns",
]
