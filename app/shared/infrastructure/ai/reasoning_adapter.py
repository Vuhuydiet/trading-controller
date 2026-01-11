import ollama
import json
from app.modules.analysis.domain.ports import MarketReasonerPort

class OllamaLlamaAdapter(MarketReasonerPort):
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    # Đổi return type thành dict
    async def explain_market_trend(self, news: str, price_change: float = 0) -> dict:
        prompt = f"""
        You are a crypto market expert. Analyze this context:
        {news}
        
        Task:
        1. Predict the price trend for the next 24h (UP, DOWN, or NEUTRAL).
        2. Explain why briefly.
        
        ⚠️ RESPONSE FORMAT: You must return ONLY a JSON object. No markdown, no intro.
        {{
            "trend": "UP", 
            "reasoning": "Because..."
        }}
        """
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt}
            ])
            content = response['message']['content']
            
            # Mẹo: Lọc lấy phần JSON nếu AI lỡ nói nhảm
            start = content.find('{')
            end = content.rfind('}') + 1
            return json.loads(content[start:end])
        except Exception:
            return {"trend": "NEUTRAL", "reasoning": "AI Analysis Failed"}