from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.infrastructure.db import get_session
from .dtos import RegisterRequest
from .handler import RegisterHandler

router = APIRouter()

@router.post("/register")
def register_endpoint(
    payload: RegisterRequest, 
    session: Session = Depends(get_session)
):
    try:
        handler = RegisterHandler(session)
        handler.handle(payload)
        return {"msg": "User created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))