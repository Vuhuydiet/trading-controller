"""
AI Model Factory - Config-based model selection

This factory allows you to swap AI models by changing config without code changes.
Supports multiple providers: FinBERT, OpenAI, Gemini, Ollama, etc.
"""

from functools import lru_cache
from app.shared.core.config import settings
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, MarketReasonerPort


def get_sentiment_analyzer() -> SentimentAnalyzerPort:
    """
    Get sentiment analyzer based on config.

    Config: AI_SENTIMENT_MODEL
    - "finbert" → FinBertAdapter (default)
    - "openai" → OpenAISentimentAdapter (future)
    - "ensemble" → EnsembleSentimentAdapter (future)

    Returns:
        SentimentAnalyzerPort instance
    """
    model_type = settings.AI_SENTIMENT_MODEL.lower()

    if model_type == "finbert":
        from app.shared.infrastructure.ai.sentiment_adapter import get_finbert_adapter_instance
        return get_finbert_adapter_instance()

    # Future: Add more models here
    # elif model_type == "openai":
    #     from app.shared.infrastructure.ai.openai_sentiment_adapter import OpenAISentimentAdapter
    #     return OpenAISentimentAdapter()
    #
    # elif model_type == "ensemble":
    #     from app.shared.infrastructure.ai.ensemble_adapter import EnsembleSentimentAdapter
    #     return EnsembleSentimentAdapter()

    else:
        # Default fallback
        print(f"Warning: Unknown sentiment model '{model_type}', falling back to FinBERT")
        from app.shared.infrastructure.ai.sentiment_adapter import get_finbert_adapter_instance
        return get_finbert_adapter_instance()


def get_market_reasoner() -> MarketReasonerPort:
    """
    Get market reasoner based on config.

    Config:
    - AI_REASONING_PROVIDER: ollama | openai | gemini
    - AI_REASONING_MODEL: llama3.2 | gpt-4 | gemini-pro

    Returns:
        MarketReasonerPort instance
    """
    provider = settings.AI_REASONING_PROVIDER.lower()

    if provider == "ollama":
        from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
        return OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL)

    # Future: Add more providers here
    # elif provider == "openai":
    #     from app.shared.infrastructure.ai.openai_reasoning_adapter import OpenAIReasoningAdapter
    #     return OpenAIReasoningAdapter(model=settings.AI_REASONING_MODEL)
    #
    # elif provider == "gemini":
    #     from app.shared.infrastructure.ai.gemini_adapter import GeminiAdapter
    #     return GeminiAdapter(model=settings.AI_REASONING_MODEL)

    else:
        # Default fallback
        print(f"Warning: Unknown reasoning provider '{provider}', falling back to Ollama")
        from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
        return OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL)


# Usage example:
# ---------------
# Instead of:
#   sentiment_bot = get_finbert_adapter_instance()
#   reasoning_bot = OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL)
#
# Use:
#   sentiment_bot = get_sentiment_analyzer()
#   reasoning_bot = get_market_reasoner()
#
# Now you can change models just by editing .env:
#   AI_SENTIMENT_MODEL=openai
#   AI_REASONING_PROVIDER=gemini
#   AI_REASONING_MODEL=gemini-pro
