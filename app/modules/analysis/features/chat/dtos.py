# app/modules/analysis/features/chat/dtos.py
from pydantic import BaseModel
from typing import List, Optional

class UserIntent(BaseModel):
    intent_type: str  # "price_check", "market_insight", "comparison", "general_chat"
    symbols: List[str]  # ["BTCUSDT", "ETHUSDT"]
    period: str = "24h" # "1h", "4h", "24h"
    
class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    reply: str
    data_sources: List[str] # Để hiển thị reference cho uy tín