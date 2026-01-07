from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from app.modules.identity.public_api import get_current_user_dto
from .dtos import BuySubscriptionRequest
from .handler import BuySubscriptionHandler

router = APIRouter()

@router.post("/subscribe")
def buy_subscription(
    payload: BuySubscriptionRequest,
    user = Depends(get_current_user_dto), # Lấy user từ token
    session: Session = Depends(get_session)
):
    try:
        handler = BuySubscriptionHandler(session)
        return handler.handle(user_id=user.id, plan_id=payload.plan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))