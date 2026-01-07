# app/modules/subscription/features/get_plans/router.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from .handler import GetPlansHandler
from app.modules.subscription.domain.plan import SubscriptionPlan 
from typing import List

router = APIRouter()

@router.get("/plans", response_model=List[SubscriptionPlan])
def get_plans(session: Session = Depends(get_session)):
    handler = GetPlansHandler(session)
    return handler.handle()