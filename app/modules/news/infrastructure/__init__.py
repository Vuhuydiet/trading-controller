"""News module infrastructure layer"""

from app.modules.news.infrastructure.crawlers import (
    BloombergCrawler,
    CoinDeskCrawler,
    ReutersCrawler,
    TwitterCrawler,
)
from app.modules.news.infrastructure.llm_adapter import (
    AnthropicInsightParser,
    LLMInsightParser,
    OllamaInsightParser,
    OpenAIInsightParser,
    get_llm_adapter,
)
from app.modules.news.infrastructure.mongo_connection import MongoDB, get_mongodb
from app.modules.news.infrastructure.pipeline import NewsPipeline
from app.modules.news.infrastructure.repository import (
    MongoInsightRepository,
    MongoNewsRepository,
)

__all__ = [
    "MongoDB",
    "get_mongodb",
    "MongoNewsRepository",
    "MongoInsightRepository",
    "CoinDeskCrawler",
    "ReutersCrawler",
    "BloombergCrawler",
    "TwitterCrawler",
    "LLMInsightParser",
    "OllamaInsightParser",
    "OpenAIInsightParser",
    "AnthropicInsightParser",
    "get_llm_adapter",
    "NewsPipeline",
]
