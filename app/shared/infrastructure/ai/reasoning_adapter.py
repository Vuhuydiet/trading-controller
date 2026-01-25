from venv import logger
import httpx
import ollama
import json
from app.modules.analysis.domain.ports import MarketReasonerPort, ReasoningResult

class OllamaLlamaAdapter(MarketReasonerPort):
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    async def explain_market_trend(self, news: str, price_change: float = 0) -> ReasoningResult:
        """
        Explain market trend using Ollama LLM.

        Args:
            news: News content or aligned context
            price_change: Price change percentage (optional, currently unused)

        Returns:
            ReasoningResult with trend prediction and reasoning
        """ 
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
            response = ollama.chat(
                model=self.model_name, 
                messages=[{'role': 'user', 'content': prompt}],
                format='json' 
            )
            content = response['message']['content']

            logger.info(f"AI Raw Response: {content}")

            # Vì đã có format='json', ta có thể parse thẳng luôn
            parsed = json.loads(content)

            return ReasoningResult(
                trend=parsed.get('trend', 'NEUTRAL'),
                reasoning=parsed.get('reasoning', 'No explanation provided')
            )
        except Exception as e:
            # Fallback in case of error
            return ReasoningResult(
                trend="NEUTRAL",
                reasoning=f"AI Analysis Failed: {str(e)}"
            )
        
    async def extract_intent(self, user_message: str) -> dict:
        prompt = f"""
        User Question: "{user_message}"
        
        Extract the user's intent and target cryptocurrency symbols (convert to Binance format e.g. BTC -> BTCUSDT).
        
        Supported intents:
        - "price_check": Asking for current price.
        - "market_insight": Asking for analysis, reasons, news, trends.
        - "comparison": Comparing 2 or more coins.
        - "general_chat": Hello, who are you, etc.

        ⚠️ RETURN JSON ONLY:
        {{
            "intent_type": "...",
            "symbols": ["BTCUSDT", "ETHUSDT"], 
            "period": "24h"
        }}
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            content = response['message']['content']
            logger.info(f"AI Intent Extraction Response: {content}")

            parsed = json.loads(content)
            return {
                "intent_type": parsed.get("intent_type", "general_chat"),
                "symbols": parsed.get("symbols", []),
                "period": parsed.get("period", "24h")
            }
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            return {
                "intent_type": "general_chat",
                "symbols": [],
                "period": "24h"
            }
        
        # --- THÊM HÀM NÀY VÀO ---
    async def chat(self, prompt: str) -> str:
        """
        Hàm này nhận prompt text và trả về text trả lời tự nhiên từ AI
        Dùng thư viện ollama cho đồng bộ với các hàm trên.
        """
        try:
            # Gọi library ollama giống hệt 2 hàm trên, nhưng không ép format json
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                # Không cần format='json' vì bước này mình cần AI chém gió tự nhiên
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error in chat generation: {e}")
            return "Sorry, I couldn't generate a response right now."