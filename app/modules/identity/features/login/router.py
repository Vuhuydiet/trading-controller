from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from .handler import LoginHandler
from .dtos import LoginResponse

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    try:
        handler = LoginHandler(session)
        return handler.handle(username=form_data.username, password=form_data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))