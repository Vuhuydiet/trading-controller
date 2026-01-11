from sqlmodel import Session, select
from typing import List
from app.modules.subscription.domain.plan import SubscriptionPlan

class GetPlansHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self) -> List[SubscriptionPlan]:
        statement = select(SubscriptionPlan)
        plans = self.session.exec(statement).all()
        return plans