# app/modules/identity/features/register/handler.py
from sqlmodel import Session, select
from app.modules.identity.domain.user import User # Refactor từ app/models/user.py
from app.shared.infrastructure.security import get_password_hash

class RegisterHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, payload):
        # 1. Validate Business Rules (Email unique)
        statement = select(User).where(User.email == payload.email)
        if self.session.exec(statement).first():
            raise ValueError("Email already registered")

        # 2. Perform Logic
        new_user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            tier="FREE" # Default logic
        )
        
        # 3. Persist
        self.session.add(new_user)
        self.session.commit()
        return new_user