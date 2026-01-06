# app/modules/market/features/get_ai_analysis/router.py
from fastapi import APIRouter, Depends, HTTPException
from app.modules.identity.public_api import get_current_user_dto
from app.modules.market.features.get_ai_analysis.handler import GetAiAnalysisHandler

router = APIRouter()

@router.get("/ai-analysis")
def get_ai_analysis(user = Depends(get_current_user_dto)):
    # Router đóng vai trò "Translator": Lấy user tier và đưa vào handler
    try:
        handler = GetAiAnalysisHandler()
        return handler.handle(user_tier=user.tier)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Vui lòng nâng cấp VIP")