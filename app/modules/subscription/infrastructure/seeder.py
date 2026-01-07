# app/modules/subscription/infrastructure/seeder.py
from sqlmodel import Session, select
from app.modules.subscription.domain.plan import SubscriptionPlan, PlanFeature

def seed_plans(session: Session):
    # Kiểm tra xem đã có data chưa, có rồi thì thôi
    if session.exec(select(SubscriptionPlan)).first():
        return

    print("🌱 Seeding Subscription Plans...")
    
    # Gói Free
    plan_free = SubscriptionPlan(
        id="free", name="Basic", price=0, description="Cho người mới bắt đầu",
        button_text="Current Plan"
    )
    feats_free = [
        PlanFeature(text="Xem biểu đồ cơ bản", included=True, plan=plan_free),
        PlanFeature(text="Phân tích AI (Giới hạn)", included=False, plan=plan_free),
        PlanFeature(text="Hỗ trợ 24/7", included=False, plan=plan_free),
    ]

    plan_vip = SubscriptionPlan(
        id="vip", name="Pro Trader", price=59, description="Dành cho trader chuyên nghiệp",
        is_popular=True, button_text="Upgrade Now", granted_tier="VIP"
    )
    feats_vip = [
        PlanFeature(text="Xem biểu đồ nâng cao", included=True, plan=plan_vip),
        PlanFeature(text="Phân tích AI (Real-time)", included=True, plan=plan_vip),
        PlanFeature(text="Tín hiệu cá voi", included=True, plan=plan_vip),
    ]

    session.add(plan_free)
    session.add(plan_vip)
    # Lưu features
    for f in feats_free + feats_vip:
        session.add(f)
        
    session.commit()
    print("✅ Seeding Complete!")