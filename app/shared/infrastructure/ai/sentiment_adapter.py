import torch
from transformers import pipeline
from functools import lru_cache 
from app.modules.analysis.domain.ports import SentimentAnalyzerPort

class FinBertAdapter(SentimentAnalyzerPort):
    def __init__(self):
        device = 0 if torch.cuda.is_available() else -1
        print(f"⏳ Loading FinBERT model on {'GPU 🔥' if device == 0 else 'CPU ❄️'}...")
        
        self.pipe = pipeline(
            "text-classification", 
            model="ProsusAI/finbert", 
            device=device
        )

    async def analyze_sentiment(self, text: str) -> dict:
        truncated_text = text[:512]
        return self.pipe(truncated_text)[0]

@lru_cache()
def get_finbert_adapter_instance():
    return FinBertAdapter()