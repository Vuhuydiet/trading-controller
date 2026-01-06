from fastapi import APIRouter, Depends
from app.modules.identity.public_api import get_current_user_dto
from .handler import CheckChartAccessHandler

router = APIRouter()

@router.get("/chart-access")
def check_chart_access(user = Depends(get_current_user_dto)):
    handler = CheckChartAccessHandler()
    return handler.handle(user_tier=user.tier)