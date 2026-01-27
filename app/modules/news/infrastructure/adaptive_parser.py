"""
Adaptive HTML Parser with Auto-Learning Structure Detection

This module provides intelligent content extraction that:
1. Uses multiple extraction strategies (semantic, density, pattern-based)
2. Learns successful patterns per domain
3. Adapts when website structure changes
4. Falls back gracefully when primary methods fail
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """Structured content extracted from a webpage"""
    title: str
    content: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    meta_description: Optional[str] = None
    extraction_method: str = "unknown"
    confidence: float = 0.0
    selectors_used: Dict[str, str] = field(default_factory=dict)


@dataclass
class ContentBlock:
    """A potential content block with scoring"""
    element: Tag
    text: str
    score: float
    selector: str
    features: Dict[str, Any] = field(default_factory=dict)


class ContentScorer:
    """
    Scores potential content blocks using multiple features.
    Higher score = more likely to be main content.
    """

    # Positive indicators (likely main content)
    POSITIVE_TAGS = {"article", "main", "section", "div"}
    POSITIVE_CLASSES = {
        "article", "content", "post", "entry", "story", "body",
        "main", "text", "news", "blog", "single", "detail"
    }
    POSITIVE_IDS = {
        "article", "content", "post", "main", "story", "entry",
        "body", "text", "news"
    }

    # Negative indicators (unlikely to be main content)
    NEGATIVE_TAGS = {"nav", "header", "footer", "aside", "form", "script", "style"}
    NEGATIVE_CLASSES = {
        "nav", "navigation", "menu", "sidebar", "widget", "footer",
        "header", "comment", "ad", "advertisement", "social", "share",
        "related", "recommended", "popup", "modal", "cookie", "banner"
    }
    NEGATIVE_IDS = {
        "nav", "navigation", "menu", "sidebar", "footer", "header",
        "comments", "ad", "advertisement"
    }

    @classmethod
    def score_block(cls, element: Tag, total_text_length: int) -> Tuple[float, Dict[str, Any]]:
        """
        Score a content block based on multiple features.
        Returns (score, features_dict)
        """
        features: Dict[str, Any] = {}
        score = 0.0

        # Get element attributes
        tag_name = element.name.lower() if element.name else ""
        classes = set(c.lower() for c in element.get("class", []) if isinstance(c, str))
        element_id = (element.get("id") or "").lower()

        # Feature 1: Text density (text length vs HTML length)
        text = element.get_text(strip=True)
        text_length = len(text)
        html_length = len(str(element))

        if html_length > 0:
            text_density = text_length / html_length
            features["text_density"] = text_density
            score += text_density * 30  # Max ~30 points

        # Feature 2: Text length ratio to total page text
        if total_text_length > 0:
            text_ratio = text_length / total_text_length
            features["text_ratio"] = text_ratio
            score += text_ratio * 40  # Max 40 points

        # Feature 3: Paragraph count
        paragraphs = element.find_all("p")
        p_count = len(paragraphs)
        features["paragraph_count"] = p_count
        score += min(p_count * 2, 20)  # Max 20 points

        # Feature 4: Link density (penalize high link density)
        links = element.find_all("a")
        link_text_length = sum(len(a.get_text(strip=True)) for a in links)
        if text_length > 0:
            link_density = link_text_length / text_length
            features["link_density"] = link_density
            score -= link_density * 20  # Penalty up to -20

        # Feature 5: Semantic tags
        if tag_name in cls.POSITIVE_TAGS:
            score += 10
            features["positive_tag"] = True

        if tag_name in cls.NEGATIVE_TAGS:
            score -= 30
            features["negative_tag"] = True

        # Feature 6: Class/ID indicators
        positive_class_matches = classes & cls.POSITIVE_CLASSES
        negative_class_matches = classes & cls.NEGATIVE_CLASSES

        if positive_class_matches:
            score += len(positive_class_matches) * 15
            features["positive_classes"] = list(positive_class_matches)

        if negative_class_matches:
            score -= len(negative_class_matches) * 20
            features["negative_classes"] = list(negative_class_matches)

        # Feature 7: ID indicators
        for pos_id in cls.POSITIVE_IDS:
            if pos_id in element_id:
                score += 15
                features["positive_id"] = element_id
                break

        for neg_id in cls.NEGATIVE_IDS:
            if neg_id in element_id:
                score -= 20
                features["negative_id"] = element_id
                break

        # Feature 8: Depth penalty (very nested content is less likely main)
        depth = len(list(element.parents))
        features["depth"] = depth
        if depth > 10:
            score -= (depth - 10) * 2

        # Feature 9: Word count bonus
        word_count = len(text.split())
        features["word_count"] = word_count
        if word_count > 100:
            score += 10
        if word_count > 300:
            score += 10
        if word_count > 500:
            score += 5

        features["final_score"] = score
        return score, features


class SelectorGenerator:
    """Generates CSS selectors for elements"""

    @staticmethod
    def generate_selector(element: Tag) -> str:
        """Generate a unique CSS selector for an element"""
        parts = []
        current = element

        while current and current.name:
            selector_part = current.name

            # Add ID if present
            if current.get("id"):
                selector_part = f"{current.name}#{current['id']}"
                parts.insert(0, selector_part)
                break  # ID is unique, stop here

            # Add classes
            classes = current.get("class", [])
            if classes:
                # Filter out dynamic/generated classes
                static_classes = [
                    c for c in classes
                    if not re.match(r"^(js-|_|css-|sc-|emotion-)", c)
                    and not re.match(r"^[a-f0-9]{6,}$", c)  # Hash-like classes
                ]
                if static_classes:
                    selector_part += "." + ".".join(static_classes[:2])

            # Add position if needed
            if current.parent:
                siblings = [
                    s for s in current.parent.children
                    if isinstance(s, Tag) and s.name == current.name
                ]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    selector_part += f":nth-of-type({index})"

            parts.insert(0, selector_part)
            current = current.parent

            if len(parts) > 4:  # Limit selector depth
                break

        return " > ".join(parts)


class AdaptiveHTMLParser:
    """
    Main adaptive parser that combines multiple extraction strategies.
    """

    def __init__(self, learned_patterns: Optional[Dict[str, Any]] = None):
        """
        Initialize parser with optional pre-learned patterns.

        Args:
            learned_patterns: Dict mapping domain to learned selectors
        """
        self.learned_patterns = learned_patterns or {}
        self.scorer = ContentScorer()
        self.selector_gen = SelectorGenerator()

    def parse(self, html: str, url: str) -> ExtractedContent:
        """
        Parse HTML and extract content using adaptive strategies.

        Extraction order:
        1. Try learned patterns for this domain
        2. Try semantic extraction (article, main tags)
        3. Try metadata-based extraction (schema.org, OpenGraph)
        4. Fall back to content density analysis
        """
        soup = BeautifulSoup(html, "html.parser")
        domain = urlparse(url).netloc

        # Strategy 1: Use learned patterns
        if domain in self.learned_patterns:
            result = self._extract_with_patterns(soup, domain)
            if result and result.confidence > 0.7:
                logger.info(f"Extracted using learned patterns for {domain}")
                return result

        # Strategy 2: Semantic extraction
        result = self._extract_semantic(soup)
        if result and result.confidence > 0.6:
            logger.info(f"Extracted using semantic tags")
            return result

        # Strategy 3: Metadata extraction
        result = self._extract_from_metadata(soup, url)
        if result and result.confidence > 0.5:
            logger.info(f"Extracted using metadata")
            return result

        # Strategy 4: Content density analysis (most adaptive)
        result = self._extract_by_density(soup)
        if result:
            logger.info(f"Extracted using density analysis")
            return result

        # Fallback: Basic extraction
        return self._extract_basic(soup, url)

    def _extract_with_patterns(
        self, soup: BeautifulSoup, domain: str
    ) -> Optional[ExtractedContent]:
        """Extract content using previously learned patterns"""
        patterns = self.learned_patterns.get(domain, {})
        if not patterns:
            return None

        try:
            title = ""
            content = ""
            author = None
            published_at = None

            # Try title selectors
            for selector in patterns.get("title_selectors", []):
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    break

            # Try content selectors
            for selector in patterns.get("content_selectors", []):
                elem = soup.select_one(selector)
                if elem:
                    content = self._clean_content(elem)
                    break

            # Try author selectors
            for selector in patterns.get("author_selectors", []):
                elem = soup.select_one(selector)
                if elem:
                    author = elem.get_text(strip=True)
                    break

            # Try date selectors
            for selector in patterns.get("date_selectors", []):
                elem = soup.select_one(selector)
                if elem:
                    published_at = self._parse_date(elem)
                    break

            if title and content and len(content) > 100:
                return ExtractedContent(
                    title=title,
                    content=content,
                    author=author,
                    published_at=published_at,
                    extraction_method="learned_patterns",
                    confidence=0.9,
                    selectors_used=patterns,
                )
        except Exception as e:
            logger.warning(f"Pattern extraction failed: {e}")

        return None

    def _extract_semantic(self, soup: BeautifulSoup) -> Optional[ExtractedContent]:
        """Extract using semantic HTML5 tags"""
        selectors_used = {}

        # Find title
        title = ""
        title_candidates = [
            soup.find("h1"),
            soup.find("meta", {"property": "og:title"}),
            soup.find("title"),
        ]
        for candidate in title_candidates:
            if candidate:
                if candidate.name == "meta":
                    title = candidate.get("content", "")
                else:
                    title = candidate.get_text(strip=True)
                if title:
                    selectors_used["title"] = self.selector_gen.generate_selector(candidate) if isinstance(candidate, Tag) else "meta[property=og:title]"
                    break

        # Find main content using semantic tags
        content = ""
        content_element = None

        semantic_selectors = [
            "article",
            "main article",
            "[role='main']",
            ".article-body",
            ".post-content",
            ".entry-content",
            ".story-body",
            "main",
        ]

        for selector in semantic_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = self._clean_content(elem)
                if len(text) > 200:
                    content = text
                    content_element = elem
                    selectors_used["content"] = selector
                    break

        if not content:
            return None

        # Find author
        author = None
        author_selectors = [
            "[rel='author']",
            ".author",
            ".byline",
            "meta[name='author']",
            "[itemprop='author']",
        ]
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == "meta":
                    author = elem.get("content", "")
                else:
                    author = elem.get_text(strip=True)
                if author:
                    selectors_used["author"] = selector
                    break

        # Find published date
        published_at = None
        date_selectors = [
            "time[datetime]",
            "[itemprop='datePublished']",
            "meta[property='article:published_time']",
            ".date",
            ".published",
        ]
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                published_at = self._parse_date(elem)
                if published_at:
                    selectors_used["date"] = selector
                    break

        if title and content:
            return ExtractedContent(
                title=title,
                content=content,
                author=author,
                published_at=published_at,
                extraction_method="semantic",
                confidence=0.8,
                selectors_used=selectors_used,
            )

        return None

    def _extract_from_metadata(
        self, soup: BeautifulSoup, url: str
    ) -> Optional[ExtractedContent]:
        """Extract from structured metadata (JSON-LD, OpenGraph, etc.)"""

        # Try JSON-LD
        json_ld = soup.find("script", {"type": "application/ld+json"})
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string or "")

                # Handle array of items
                if isinstance(data, list):
                    data = next(
                        (d for d in data if d.get("@type") in ["NewsArticle", "Article", "BlogPosting"]),
                        data[0] if data else {}
                    )

                if data.get("@type") in ["NewsArticle", "Article", "BlogPosting"]:
                    title = data.get("headline", "")
                    content = data.get("articleBody", "")
                    author = data.get("author", {})
                    if isinstance(author, dict):
                        author = author.get("name", "")
                    elif isinstance(author, list):
                        author = author[0].get("name", "") if author else ""

                    date_str = data.get("datePublished", "")
                    published_at = self._parse_date_string(date_str) if date_str else None

                    if title and content:
                        return ExtractedContent(
                            title=title,
                            content=content,
                            author=author if isinstance(author, str) else None,
                            published_at=published_at,
                            extraction_method="json_ld",
                            confidence=0.85,
                            selectors_used={"method": "json-ld"},
                        )
            except Exception as e:
                logger.debug(f"JSON-LD parsing failed: {e}")

        # Try OpenGraph
        og_title = soup.find("meta", {"property": "og:title"})
        og_description = soup.find("meta", {"property": "og:description"})

        if og_title and og_description:
            title = og_title.get("content", "")
            # OG description is usually a summary, try to get full content elsewhere
            meta_desc = og_description.get("content", "")

            # Find body content
            article = soup.find("article") or soup.find("main")
            if article:
                content = self._clean_content(article)
            else:
                content = meta_desc

            if title and len(content) > 100:
                return ExtractedContent(
                    title=title,
                    content=content,
                    meta_description=meta_desc,
                    extraction_method="opengraph",
                    confidence=0.6,
                    selectors_used={"method": "opengraph"},
                )

        return None

    def _extract_by_density(self, soup: BeautifulSoup) -> Optional[ExtractedContent]:
        """
        Extract content by analyzing text density across page blocks.
        This is the most adaptive method - works on any page structure.
        """
        # Get total text length for ratio calculations
        body = soup.find("body") or soup
        total_text = body.get_text(strip=True)
        total_text_length = len(total_text)

        if total_text_length < 100:
            return None

        # Find all potential content blocks
        blocks: List[ContentBlock] = []

        # Consider divs, sections, articles with substantial text
        for tag in ["article", "section", "div", "main"]:
            for elem in soup.find_all(tag):
                text = elem.get_text(strip=True)
                if len(text) > 200:  # Minimum content threshold
                    score, features = self.scorer.score_block(elem, total_text_length)
                    selector = self.selector_gen.generate_selector(elem)
                    blocks.append(ContentBlock(
                        element=elem,
                        text=text,
                        score=score,
                        selector=selector,
                        features=features,
                    ))

        if not blocks:
            return None

        # Sort by score and get best candidate
        blocks.sort(key=lambda b: b.score, reverse=True)
        best_block = blocks[0]

        # Extract title
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            # Try the title tag
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
                # Clean up common title suffixes
                title = re.split(r"\s*[|\-–—]\s*", title)[0].strip()

        # Clean content
        content = self._clean_content(best_block.element)

        # Try to find author and date in the best block or nearby
        author = self._find_author_near(best_block.element, soup)
        published_at = self._find_date_near(best_block.element, soup)

        # Calculate confidence based on score
        max_possible_score = 100  # Approximate max score
        confidence = min(best_block.score / max_possible_score, 1.0)
        confidence = max(confidence, 0.3)  # Minimum confidence

        return ExtractedContent(
            title=title,
            content=content,
            author=author,
            published_at=published_at,
            extraction_method="density_analysis",
            confidence=confidence,
            selectors_used={
                "content": best_block.selector,
                "score": best_block.score,
                "features": best_block.features,
            },
        )

    def _extract_basic(self, soup: BeautifulSoup, url: str) -> ExtractedContent:
        """Basic fallback extraction when all else fails"""
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        # Get all paragraph text
        paragraphs = soup.find_all("p")
        content = "\n\n".join(
            p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50
        )

        return ExtractedContent(
            title=title or "Untitled",
            content=content or "No content extracted",
            extraction_method="basic_fallback",
            confidence=0.2,
            selectors_used={"method": "paragraph_collection"},
        )

    def _clean_content(self, element: Tag) -> str:
        """Clean and extract text from an element"""
        # Remove unwanted elements
        for unwanted in element.find_all(
            ["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]
        ):
            unwanted.decompose()

        # Remove elements with negative indicators
        for cls in ContentScorer.NEGATIVE_CLASSES:
            for elem in element.find_all(class_=re.compile(cls, re.I)):
                elem.decompose()

        # Get text with paragraph structure
        paragraphs = []
        for p in element.find_all(["p", "h2", "h3", "h4", "blockquote"]):
            text = p.get_text(strip=True)
            if len(text) > 20:
                paragraphs.append(text)

        if paragraphs:
            return "\n\n".join(paragraphs)

        # Fallback to all text
        return element.get_text(separator="\n", strip=True)

    def _find_author_near(self, content_elem: Tag, soup: BeautifulSoup) -> Optional[str]:
        """Find author near the content element"""
        # Check within content element
        author_selectors = [
            "[rel='author']", ".author", ".byline", "[itemprop='author']",
            ".author-name", ".writer", ".contributor"
        ]

        for selector in author_selectors:
            elem = content_elem.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # Check parent and siblings
        parent = content_elem.parent
        if parent:
            for selector in author_selectors:
                elem = parent.select_one(selector)
                if elem:
                    return elem.get_text(strip=True)

        # Check meta
        meta_author = soup.find("meta", {"name": "author"})
        if meta_author:
            return meta_author.get("content", "")

        return None

    def _find_date_near(self, content_elem: Tag, soup: BeautifulSoup) -> Optional[datetime]:
        """Find publication date near the content element"""
        date_selectors = [
            "time[datetime]", "[itemprop='datePublished']", ".date",
            ".published", ".post-date", ".entry-date", ".timestamp"
        ]

        # Check within and near content
        for elem_to_check in [content_elem, content_elem.parent, soup]:
            if elem_to_check is None:
                continue
            for selector in date_selectors:
                elem = elem_to_check.select_one(selector) if hasattr(elem_to_check, 'select_one') else None
                if elem:
                    result = self._parse_date(elem)
                    if result:
                        return result

        # Check meta
        meta_date = soup.find("meta", {"property": "article:published_time"})
        if meta_date:
            return self._parse_date_string(meta_date.get("content", ""))

        return None

    def _parse_date(self, element: Tag) -> Optional[datetime]:
        """Parse date from an element"""
        # Try datetime attribute first
        if element.get("datetime"):
            return self._parse_date_string(element["datetime"])
        if element.get("content"):
            return self._parse_date_string(element["content"])

        # Try text content
        text = element.get_text(strip=True)
        return self._parse_date_string(text)

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse various date string formats"""
        if not date_str:
            return None

        # Common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        # Clean up the string
        date_str = date_str.strip()
        date_str = re.sub(r"\s+", " ", date_str)

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        # Try ISO format with fromisoformat
        try:
            # Handle Z timezone
            date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str)
        except ValueError:
            pass

        return None

    def learn_from_success(
        self, url: str, extracted: ExtractedContent, verified: bool = True
    ) -> Dict[str, Any]:
        """
        Learn from successful extraction to improve future parsing.
        Returns the learned pattern for storage.
        """
        if not verified or extracted.confidence < 0.5:
            return {}

        domain = urlparse(url).netloc

        # Build pattern from used selectors
        pattern = {
            "domain": domain,
            "learned_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": extracted.extraction_method,
            "confidence": extracted.confidence,
            "title_selectors": [],
            "content_selectors": [],
            "author_selectors": [],
            "date_selectors": [],
        }

        selectors = extracted.selectors_used

        # Store content selector
        if "content" in selectors:
            pattern["content_selectors"].append(selectors["content"])

        # For semantic/density methods, also store the common selectors
        if extracted.extraction_method in ["semantic", "density_analysis"]:
            if selectors.get("title"):
                pattern["title_selectors"].append(selectors["title"])
            if selectors.get("author"):
                pattern["author_selectors"].append(selectors["author"])
            if selectors.get("date"):
                pattern["date_selectors"].append(selectors["date"])

        # Update internal patterns
        if domain not in self.learned_patterns:
            self.learned_patterns[domain] = pattern
        else:
            # Merge with existing patterns
            existing = self.learned_patterns[domain]
            for key in ["title_selectors", "content_selectors", "author_selectors", "date_selectors"]:
                existing[key] = list(set(existing.get(key, []) + pattern.get(key, [])))[:5]
            existing["learned_at"] = pattern["learned_at"]
            existing["confidence"] = max(existing.get("confidence", 0), pattern["confidence"])

        return pattern


def get_adaptive_parser(learned_patterns: Optional[Dict[str, Any]] = None) -> AdaptiveHTMLParser:
    """Factory function to get parser instance"""
    return AdaptiveHTMLParser(learned_patterns)
