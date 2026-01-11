import torch
from transformers import pipeline
from functools import lru_cache
from app.modules.analysis.domain.ports import SentimentAnalyzerPort, SentimentResult

class FinBertAdapter(SentimentAnalyzerPort):
    def __init__(self):
        device = 0 if torch.cuda.is_available() else -1
        device_name = 'GPU' if device == 0 else 'CPU'
        print(f"Loading FinBERT model on {device_name}...")

        self.pipe = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            device=device
        )

    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment using FinBERT model.

        Args:
            text: Input text to analyze (will be truncated to 512 chars)

        Returns:
            SentimentResult with label and confidence score
        """
        truncated_text = text[:512]
        result = self.pipe(truncated_text)[0]

        # Convert to standardized format
        return SentimentResult(
            label=result['label'],
            score=result['score']
        )

@lru_cache()
def get_finbert_adapter_instance():
    return FinBertAdapter()