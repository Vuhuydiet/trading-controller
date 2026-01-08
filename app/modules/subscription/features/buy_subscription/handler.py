from sqlmodel import Session
from app.modules.identity.public_api import upgrade_user_to_vip
from app.modules.subscription.domain.plan import SubscriptionPlan

from app.modules.subscription.domain.plan import SubscriptionPlan
from app.modules.identity.public_api import set_user_tier 

class BuySubscriptionHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, user_id: int, plan_id: str):
        # 1. Lấy thông tin gói từ DB của Subscription
        plan = self.session.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError("Plan not found")

        # 2. Gọi sang Identity để update
        # Subscription chỉ ra lệnh: "Set tier này cho user kia", không quan tâm bảng User
        is_updated = set_user_tier(self.session, user_id, plan.granted_tier)
        
        if not is_updated:
            raise ValueError("User not found")

        # 3. Commit Transaction
        # Lúc này session sẽ lưu cả thay đổi bên User (Identity) và Plan (nếu có log history)
        self.session.commit()
        
        return {
            "msg": f"Upgraded to {plan.name}", 
            "current_tier": plan.granted_tier
        }