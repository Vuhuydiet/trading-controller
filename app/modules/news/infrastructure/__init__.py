"""News module infrastructure layer"""

from app.modules.news.infrastructure.crawlers import (
    AdaptiveCrawlerMixin,
    BloombergCrawler,
    CoinDeskCrawler,
    ReutersCrawler,
    TwitterCrawler,
    create_crawlers_with_patterns,
)
from app.modules.news.infrastructure.llm_adapter import (
    AnthropicInsightParser,
    LLMInsightParser,
    OllamaInsightParser,
    OpenAIInsightParser,
    get_llm_adapter,
)
from app.modules.news.infrastructure.adaptive_parser import (
    AdaptiveHTMLParser,
    ContentScorer,
    ExtractedContent,
    get_adaptive_parser,
)
from app.modules.news.infrastructure.structure_learner import (
    ExtractionLog,
    LearnedPattern,
    StructureLearner,
    get_structure_learner,
)

__all__ = [
    # Crawlers
    "CoinDeskCrawler",
    "ReutersCrawler",
    "BloombergCrawler",
    "TwitterCrawler",
    "AdaptiveCrawlerMixin",
    "create_crawlers_with_patterns",
    # Adaptive Parser
    "AdaptiveHTMLParser",
    "ContentScorer",
    "ExtractedContent",
    "get_adaptive_parser",
    # Structure Learner
    "LearnedPattern",
    "ExtractionLog",
    "StructureLearner",
    "get_structure_learner",
    # LLM Adapters
    "LLMInsightParser",
    "OllamaInsightParser",
    "OpenAIInsightParser",
    "AnthropicInsightParser",
    "get_llm_adapter",
]
