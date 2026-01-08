from sqlmodel import Session, select, or_
from app.modules.identity.domain.user import User
from app.shared.infrastructure.security import get_password_hash

class RegisterHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, payload):
        # Check Username hoặc Email đã tồn tại chưa
        statement = select(User).where(
            or_(User.username == payload.username)
        )
        if self.session.exec(statement).first():
            raise ValueError("Username already registered")

        new_user = User(
            username=payload.username,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            tier="FREE"
        )
        
        self.session.add(new_user)
        self.session.commit()
        return new_user