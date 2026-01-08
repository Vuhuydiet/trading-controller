from sqlmodel import Session
from app.modules.identity.domain.user import User

class GetMeHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, user_id: int):
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        return user