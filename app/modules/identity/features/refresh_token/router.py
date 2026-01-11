from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from .dtos import RefreshTokenRequest, RefreshTokenResponse
from .handler import RefreshTokenHandler

router = APIRouter()

@router.post("/refresh-token", response_model=RefreshTokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    session: Session = Depends(get_session)
):
    try:
        handler = RefreshTokenHandler(session)
        return handler.handle(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))