from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordRequestForm
from app.core.db import get_session
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth import RegisterRequest

router = APIRouter()

@router.post("/register")
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):
    email = payload.email
    password = payload.password

    statement = select(User).where(User.email == email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
    )
    session.add(new_user)
    session.commit()

    return {"msg": "User created successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Tạo token
    access_token = create_access_token(subject=user.id, tier=user.tier)
    return {"access_token": access_token, "token_type": "bearer"}