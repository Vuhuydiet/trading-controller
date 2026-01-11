import json
import logging
from typing import Optional, Any

from app.modules.news.domain.article import NewsArticle, NewsInsight
from app.modules.news.domain.ports import LLMAdapter
from app.shared.core.config import settings

logger = logging.getLogger(__name__)


class LLMInsightParser(LLMAdapter):
    """Base class for LLM integration to parse articles"""

    async def parse_article_to_insight(self, article: NewsArticle) -> NewsInsight:
        """Parse article using LLM"""
        raise NotImplementedError


class OllamaInsightParser(LLMInsightParser):
    """Ollama-based insight parser (local LLM)"""

    def __init__(self, model: str = "llama2"):
        self.model = model
        try:
            import ollama

            self.client: Optional[Any] = ollama
        except ImportError:
            logger.error("Ollama package not installed")
            self.client = None

    async def parse_article_to_insight(self, article: NewsArticle) -> NewsInsight:
        """Parse article using Ollama"""

        if not self.client:
            return self._create_basic_insight(article, "ollama")

        try:
            prompt = self._create_prompt(article)

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
            )

            result = self._parse_response(response["response"], article)
            result.llm_model_used = self.model
            return result

        except Exception as e:
            logger.error(f"Error parsing article with Ollama: {str(e)}")
            return self._create_basic_insight(article, "ollama")

    def _create_prompt(self, article: NewsArticle) -> str:
        """Create prompt for LLM"""
        return f"""Analyze the following cryptocurrency news article and provide insights in JSON format:

Title: {article.title}
Content: {article.content[:2000]}

Please provide a JSON response with the following structure (and ONLY this JSON, no other text):
{{
    "cryptocurrency_mentioned": ["list of cryptos mentioned"],
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.5,
    "key_points": ["important points"],
    "market_impact": "bullish/bearish/neutral or description",
    "entities": {{"entities_type": ["list of named entities"]}},
    "tags": ["topic tags"],
    "summary": "brief summary"
}}

Return only valid JSON."""

    def _parse_response(self, response: str, article: NewsArticle) -> NewsInsight:
        """Parse LLM response"""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            data = json.loads(json_str.strip())

            return NewsInsight(
                article_id=article.id or "unknown",
                source=article.source,
                cryptocurrency_mentioned=data.get("cryptocurrency_mentioned", []),
                sentiment=data.get("sentiment", "neutral"),
                sentiment_score=data.get("sentiment_score", 0.0),
                key_points=data.get("key_points", []),
                market_impact=data.get("market_impact", ""),
                entities=data.get("entities", {}),
                tags=data.get("tags", []),
                summary=data.get("summary", ""),
                raw_analysis=data,
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._create_basic_insight(article, "ollama")

    def _create_basic_insight(self, article: NewsArticle, model: str) -> NewsInsight:
        """Create basic insight when LLM parsing fails"""
        return NewsInsight(
            article_id=article.id or "unknown",
            source=article.source,
            sentiment="neutral",
            sentiment_score=0.0,
            summary=article.title,
            llm_model_used=model,
        )


class OpenAIInsightParser(LLMInsightParser):
    """OpenAI-based insight parser"""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            self.client: Optional[Any] = None
        else:
            try:
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed")
                self.client = None

    async def parse_article_to_insight(self, article: NewsArticle) -> NewsInsight:
        """Parse article using OpenAI"""

        if not self.client:
            return self._create_basic_insight(article, self.model)

        try:
            prompt = self._create_prompt(article)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial news analyst specialized in cryptocurrency market analysis.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            result = self._parse_response(response.choices[0].message.content or "", article)
            result.llm_model_used = self.model
            return result

        except Exception as e:
            logger.error(f"Error parsing article with OpenAI: {str(e)}")
            return self._create_basic_insight(article, self.model)

    def _create_prompt(self, article: NewsArticle) -> str:
        """Create prompt for OpenAI"""
        return f"""Analyze the following cryptocurrency news article and provide insights in JSON format:

Title: {article.title}
Content: {article.content[:2000]}

Please provide a JSON response with the following structure (and ONLY this JSON, no other text):
{{
    "cryptocurrency_mentioned": ["list of cryptos mentioned"],
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.5,
    "key_points": ["important points"],
    "market_impact": "bullish/bearish/neutral or description",
    "entities": {{"entities_type": ["list of named entities"]}},
    "tags": ["topic tags"],
    "summary": "brief summary"
}}

Return only valid JSON."""

    def _parse_response(self, response: str, article: NewsArticle) -> NewsInsight:
        """Parse LLM response"""
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            data = json.loads(json_str.strip())

            return NewsInsight(
                article_id=article.id or "unknown",
                source=article.source,
                cryptocurrency_mentioned=data.get("cryptocurrency_mentioned", []),
                sentiment=data.get("sentiment", "neutral"),
                sentiment_score=data.get("sentiment_score", 0.0),
                key_points=data.get("key_points", []),
                market_impact=data.get("market_impact", ""),
                entities=data.get("entities", {}),
                tags=data.get("tags", []),
                summary=data.get("summary", ""),
                raw_analysis=data,
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._create_basic_insight(article, self.model)

    def _create_basic_insight(self, article: NewsArticle, model: str) -> NewsInsight:
        """Create basic insight when LLM parsing fails"""
        return NewsInsight(
            article_id=article.id or "unknown",
            source=article.source,
            sentiment="neutral",
            sentiment_score=0.0,
            summary=article.title,
            llm_model_used=model,
        )


class AnthropicInsightParser(LLMInsightParser):
    """Anthropic Claude-based insight parser"""

    def __init__(self, model: str = "claude-3-haiku-20240307"):
        self.model = model
        self.api_key = settings.ANTHROPIC_API_KEY
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            self.client: Optional[Any] = None
        else:
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("Anthropic package not installed")
                self.client = None

    async def parse_article_to_insight(self, article: NewsArticle) -> NewsInsight:
        """Parse article using Anthropic"""

        if not self.client:
            return self._create_basic_insight(article, self.model)

        try:
            prompt = self._create_prompt(article)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            result = self._parse_response(response.content[0].text, article)
            result.llm_model_used = self.model
            return result

        except Exception as e:
            logger.error(f"Error parsing article with Anthropic: {str(e)}")
            return self._create_basic_insight(article, self.model)

    def _create_prompt(self, article: NewsArticle) -> str:
        """Create prompt for Anthropic"""
        return f"""Analyze the following cryptocurrency news article and provide insights in JSON format:

Title: {article.title}
Content: {article.content[:2000]}

Please provide a JSON response with the following structure (and ONLY this JSON, no other text):
{{
    "cryptocurrency_mentioned": ["list of cryptos mentioned"],
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.5,
    "key_points": ["important points"],
    "market_impact": "bullish/bearish/neutral or description",
    "entities": {{"entities_type": ["list of named entities"]}},
    "tags": ["topic tags"],
    "summary": "brief summary"
}}

Return only valid JSON."""

    def _parse_response(self, response: str, article: NewsArticle) -> NewsInsight:
        """Parse LLM response"""
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            data = json.loads(json_str.strip())

            return NewsInsight(
                article_id=article.id or "unknown",
                source=article.source,
                cryptocurrency_mentioned=data.get("cryptocurrency_mentioned", []),
                sentiment=data.get("sentiment", "neutral"),
                sentiment_score=data.get("sentiment_score", 0.0),
                key_points=data.get("key_points", []),
                market_impact=data.get("market_impact", ""),
                entities=data.get("entities", {}),
                tags=data.get("tags", []),
                summary=data.get("summary", ""),
                raw_analysis=data,
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._create_basic_insight(article, self.model)

    def _create_basic_insight(self, article: NewsArticle, model: str) -> NewsInsight:
        """Create basic insight when LLM parsing fails"""
        return NewsInsight(
            article_id=article.id or "unknown",
            source=article.source,
            sentiment="neutral",
            sentiment_score=0.0,
            summary=article.title,
            llm_model_used=model,
        )


def get_llm_adapter(provider: Optional[str] = None) -> LLMInsightParser:
    """Factory function to get appropriate LLM adapter"""
    provider = provider or settings.LLM_PROVIDER

    if provider == "openai":
        return OpenAIInsightParser()
    elif provider == "anthropic":
        return AnthropicInsightParser()
    else:  # Default to Ollama
        return OllamaInsightParser(model=settings.LLM_MODEL)
