from pydantic import BaseModel
from typing import List

class PlanFeature(BaseModel):
    text: str
    included: bool

class Plan(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "USD"
    description: str
    features: List[PlanFeature]
    is_popular: bool = False
    button_text: str = "Get Started"