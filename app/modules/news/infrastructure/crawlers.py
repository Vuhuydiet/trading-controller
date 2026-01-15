import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx
from bs4 import BeautifulSoup, Tag

from app.modules.news.domain.article import NewsArticle, NewsSource
from app.modules.news.domain.ports import NewsCrawler

logger = logging.getLogger(__name__)


class CoinDeskCrawler(NewsCrawler):
    """Crawler for CoinDesk news"""

    BASE_URL = "https://www.coindesk.com"
    FEED_URL = "https://www.coindesk.com/feed"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from CoinDesk"""
        articles: List[NewsArticle] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try RSS feed first
                response = await client.get(self.FEED_URL)
                articles.extend(await self._parse_rss_feed(response.text, NewsSource.COINDESK))
        except Exception as e:
            logger.error(f"Error fetching CoinDesk news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single CoinDesk article"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Extract metadata
                title = soup.find("h1")
                content_divs = soup.find_all("article")
                published = soup.find("time")

                if not title or not content_divs:
                    return None

                return NewsArticle(
                    source=NewsSource.COINDESK,
                    title=title.get_text(strip=True),
                    content="\n".join([div.get_text(strip=True) for div in content_divs]),
                    url=url,
                    published_at=(
                        datetime.fromisoformat(str(published.get("datetime", "")))
                        if published and isinstance(published, Tag) and published.get("datetime")
                        else datetime.now(timezone.utc)
                    ),
                )
        except Exception as e:
            logger.error(f"Error parsing CoinDesk article {url}: {str(e)}")
            return None

    async def _parse_rss_feed(self, feed_content: str, source: NewsSource) -> List[NewsArticle]:
        """Parse RSS feed content"""
        import feedparser

        articles: List[NewsArticle] = []
        try:
            feed_result: dict[str, Any] = feedparser.parse(feed_content)
            entries: list[Any] = feed_result.get("entries") or []
            for entry in entries[:10]:  # Get latest 10
                entry_dict: dict[str, Any] = entry
                article = NewsArticle(
                    source=source,
                    title=str(entry_dict.get("title", "")),
                    content=str(entry_dict.get("summary", "")),
                    url=str(entry_dict.get("link", "")),
                    author=str(entry_dict.get("author", "")),
                    published_date=(
                        datetime.fromtimestamp(entry_dict.get("published_parsed", {}).tm_mtime)
                        if entry_dict.get("published_parsed")
                        else datetime.now(timezone.utc)
                    ),
                    status=ArticleStatus.CRAWLED,
                )
                articles.append(article)
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {str(e)}")

        return articles


class ReutersCrawler(NewsCrawler):
    """Crawler for Reuters cryptocurrency news"""

    BASE_URL = "https://www.reuters.com"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from Reuters"""
        articles: List[NewsArticle] = []
        try:
            # Reuters uses JavaScript rendering, we'll use a basic approach
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.reuters.com/finance/cryptocurrency",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract article links
                for link in soup.find_all("a", limit=10):
                    href = link.get("href")
                    if href and isinstance(href, str) and "article" in href:
                        article = await self.parse_article(self.BASE_URL + href)
                        if article:
                            articles.append(article)
        except Exception as e:
            logger.error(f"Error fetching Reuters news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single Reuters article"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                title = soup.find("h1")
                content = soup.find("article")
                published = soup.find("meta", {"name": "publish_date"})

                if not title or not content:
                    return None

                return NewsArticle(
                    source=NewsSource.REUTERS,
                    title=title.get_text(strip=True),
                    content=content.get_text(strip=True),
                    url=url,
                    published_date=(
                        datetime.fromisoformat(str(published.get("content", "")))
                        if published and isinstance(published, Tag) and published.get("content")
                        else datetime.now(timezone.utc)
                    ),
                    raw_html=response.text,
                    status=ArticleStatus.CRAWLED,
                )
        except Exception as e:
            logger.error(f"Error parsing Reuters article {url}: {str(e)}")
            return None


class BloombergCrawler(NewsCrawler):
    """Crawler for Bloomberg cryptocurrency news"""

    BASE_URL = "https://www.bloomberg.com"

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch latest news from Bloomberg"""
        articles: List[NewsArticle] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.bloomberg.com/crypto",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                soup = BeautifulSoup(response.text, "html.parser")

                for link in soup.find_all("a", limit=10):
                    href = link.get("href")
                    if href and isinstance(href, str):
                        if "/news/" in href or "/articles/" in href:
                            full_url = self.BASE_URL + href if href.startswith("/") else href
                            article = await self.parse_article(full_url)
                        if article:
                            articles.append(article)
        except Exception as e:
            logger.error(f"Error fetching Bloomberg news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single Bloomberg article"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                title = soup.find("h1")
                content = soup.find("article")
                published = soup.find("meta", {"property": "article:published_time"})

                if not title or not content:
                    return None

                return NewsArticle(
                    source=NewsSource.BLOOMBERG,
                    title=title.get_text(strip=True),
                    content=content.get_text(strip=True),
                    url=url,
                    published_date=(
                        datetime.fromisoformat(
                            str(published.get("content", "")).replace("Z", "+00:00")
                        )
                        if published and isinstance(published, Tag) and published.get("content")
                        else datetime.now(timezone.utc)
                    ),
                    raw_html=response.text,
                    status=ArticleStatus.CRAWLED,
                )
        except Exception as e:
            logger.error(f"Error parsing Bloomberg article {url}: {str(e)}")
            return None


class TwitterCrawler(NewsCrawler):
    """Crawler for cryptocurrency-related tweets"""

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
            query = "cryptocurrency OR bitcoin OR ethereum -is:retweet"
            tweets = client.search_recent_tweets(
                query=query, max_results=10, tweet_fields=["created_at", "author_id"]
            )

            if tweets.data:  # pyright: ignore[reportAttributeAccessIssue]
                for tweet in tweets.data:  # pyright: ignore[reportAttributeAccessIssue]
                    article = NewsArticle(
                        source=NewsSource.TWITTER,
                        title=f"Tweet by {tweet.author_id}",
                        content=tweet.text,
                        url=f"https://twitter.com/i/web/status/{tweet.id}",
                        published_date=tweet.created_at,
                        status=ArticleStatus.CRAWLED,
                    )
                    articles.append(article)
        except Exception as e:
            logger.error(f"Error fetching Twitter news: {str(e)}")

        return articles

    async def parse_article(self, url: str) -> Optional[NewsArticle]:
        """Parse a single tweet"""
        # Twitter articles are parsed during fetch
        return None
