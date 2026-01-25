from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.shared.infrastructure.db import get_session 

from app.modules.analysis.features.chat.dtos import ChatRequest, ChatResponse
from app.modules.analysis.features.chat.handler import ChatHandler
from app.modules.analysis.infrastructure.repository import SqlModelAnalysisRepo

# Import các adapter
from app.shared.infrastructure.ai.reasoning_adapter import OllamaLlamaAdapter
from app.modules.market.infrastructure.binance_rest_client import BinanceRestClient

router = APIRouter()

def get_chat_handler(
    session: Session = Depends(get_session)
) -> ChatHandler:
    repo = SqlModelAnalysisRepo(session)
    
    return ChatHandler(
        reasoner=OllamaLlamaAdapter(),
        price_service=BinanceRestClient(),
        repo=repo
    )

@router.post("/", response_model=ChatResponse)
async def chat_with_market_ai(
    request: ChatRequest,
    handler: ChatHandler = Depends(get_chat_handler)
):
    """
    Chat với AI về thị trường Crypto.
    """
    try:
        response = await handler.handle_chat(request.message) 
        
        return response
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))