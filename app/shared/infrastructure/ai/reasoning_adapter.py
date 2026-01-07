import ollama
from app.modules.analysis.domain.ports import MarketReasonerPort

class OllamaLlamaAdapter(MarketReasonerPort):
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    # Implement đúng hàm trong Interface
    async def explain_market_trend(self, news: str, price_change: float) -> str:
        prompt = f"""
        News: {news}
        Price Change: {price_change}%
        Explain logic connection between news and price.
        """
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content']
        except Exception:
            return "AI Analysis Failed."