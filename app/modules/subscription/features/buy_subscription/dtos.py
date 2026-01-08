from pydantic import BaseModel

class BuySubscriptionRequest(BaseModel):
    plan_id: str