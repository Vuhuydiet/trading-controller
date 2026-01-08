from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from app.modules.identity.public_api import get_current_user_dto
from .dtos import UserProfileResponse
from .handler import GetMeHandler

router = APIRouter()

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    # Lấy user_id từ Token đã decode (public api)
    current_user_dto = Depends(get_current_user_dto),
    session: Session = Depends(get_session)
):
    try:
        handler = GetMeHandler(session)
        # Query DB để lấy full thông tin
        return handler.handle(user_id=current_user_dto.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")