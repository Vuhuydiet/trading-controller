# app/modules/subscription/domain/plan.py
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from app.shared.domain.enums import UserTier 

# Bảng tính năng con (VD: "Xem biểu đồ", "AI Analysis"...)
class PlanFeature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    included: bool = True
    
    # Khóa ngoại trỏ về Plan cha
    plan_id: str = Field(foreign_key="subscriptionplan.id")
    plan: "SubscriptionPlan" = Relationship(back_populates="features")

# Bảng gói chính (Free, VIP)
class SubscriptionPlan(SQLModel, table=True):
    id: str = Field(primary_key=True) # VD: "free", "vip"
    name: str
    price: float
    currency: str = "USD"
    description: str
    is_popular: bool = False
    button_text: str = "Subscribe"
    granted_tier: UserTier = Field(default=UserTier.FREE)
    
    # Quan hệ ngược lại để lấy danh sách feature
    features: List[PlanFeature] = Relationship(back_populates="plan", sa_relationship_kwargs={"lazy": "selectin"}) 
    # lazy="selectin" giúp load luôn features khi query plan (quan trọng)