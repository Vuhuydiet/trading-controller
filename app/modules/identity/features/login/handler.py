from sqlmodel import Session, select
from fastapi import HTTPException
from app.modules.identity.domain.user import User
from app.shared.infrastructure.security import verify_password, create_access_token

class LoginHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, username, password) -> dict:
        # Logic lấy từ endpoint login cũ
        statement = select(User).where(User.email == username)
        user = self.session.exec(statement).first()

        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect email or password")

        access_token = create_access_token(subject=str(user.id), tier=user.tier)
        return {"access_token": access_token, "token_type": "bearer"}