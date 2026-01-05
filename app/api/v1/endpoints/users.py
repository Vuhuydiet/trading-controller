from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.core.db import get_session
from sqlmodel import Session

router = APIRouter()

@router.post("/upgrade-vip")
def upgrade_to_vip(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    API giả lập thanh toán: Bấm phát lên VIP luôn để test cho dễ.
    """
    if current_user.tier == "VIP":
        return {"msg": "Đại gia à, bạn đã là VIP rồi!"}
    
    current_user.tier = "VIP"
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {
        "msg": "Chúc mừng! Bạn đã nâng cấp lên tài khoản VIP thành công.",
        "tier": current_user.tier
    }