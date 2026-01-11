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
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt}
            ])
            content = response['message']['content']

            # Extract JSON from response (in case AI adds extra text)
            start = content.find('{')
            end = content.rfind('}') + 1
            parsed = json.loads(content[start:end])

            # Convert to standardized format
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