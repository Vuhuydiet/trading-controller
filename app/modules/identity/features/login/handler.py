from sqlmodel import Session, select
from app.modules.identity.domain.user import User
from app.shared.infrastructure.security import verify_password, create_access_token, create_refresh_token

class LoginHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, username, password) -> dict:
        # Tìm theo username
        statement = select(User).where(User.username == username)
        user = self.session.exec(statement).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect username or password")
        
        access_token = create_access_token(subject=str(user.id), tier=user.tier, username=user.username)
        refresh_token = create_refresh_token(subject=str(user.id)) 
        
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }