# app/modules/identity/features/forgot_password/handler.py
from sqlmodel import Session, select
from app.modules.identity.domain.user import User
from app.shared.infrastructure.security import get_password_hash

class ForgotPasswordHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, username: str):
        # 1. Tìm user theo username
        statement = select(User).where(User.username == username)
        user = self.session.exec(statement).first()
        
        if not user:
            raise ValueError("User not found")

        # 2. Reset thẳng mật khẩu về "123456"
        # Đây là cách nhanh nhất để bạn test login lại mà không cần flow email
        new_password = "123456"
        user.hashed_password = get_password_hash(new_password)
        
        # 3. Lưu vào DB
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return {
            "message": f"Password for '{username}' has been reset to '{new_password}'",
            "new_password": new_password 
        }