# app/modules/market/features/get_ai_analysis/handler.py
class GetAiAnalysisHandler:
    def handle(self, user_tier: str):
        if user_tier != "VIP":
             raise PermissionError("Upgrade to VIP to access this feature")
        
        return [
            {"coin": "BTC/USDT", "price": 94500, "trend": "bullish", "confidence": 0.92},
            {"coin": "ETH/USDT", "price": 6750, "trend": "bearish", "confidence": 0.85},
        ]