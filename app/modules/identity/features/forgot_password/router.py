from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from .dtos import ForgotPasswordRequest
from .handler import ForgotPasswordHandler

router = APIRouter()

@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session)
):
    try:
        handler = ForgotPasswordHandler(session)
        return handler.handle(payload.username)
    except ValueError as e:
        # Trong thực tế nên trả về 200 dù username sai để tránh dò user
        raise HTTPException(status_code=404, detail=str(e))