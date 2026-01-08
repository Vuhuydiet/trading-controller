from jose import jwt, JWTError
from sqlmodel import Session
from app.modules.identity.domain.user import User
from app.shared.infrastructure.security import create_access_token
from app.shared.core.config import settings

class RefreshTokenHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, refresh_token: str):
        try:
            # 1. Giải mã token
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                raise ValueError("Invalid refresh token")
            
            # 2. Query lại DB để lấy info mới nhất (QUAN TRỌNG: Để cập nhật VIP)
            user = self.session.get(User, int(user_id))
            if not user:
                raise ValueError("User not found")

            # 3. Tạo Access Token mới với tier mới nhất từ DB
            new_access_token = create_access_token(subject=user.id, tier=user.tier, username=user.username)
            
            return {"access_token": new_access_token}

        except JWTError:
            raise ValueError("Invalid refresh token")