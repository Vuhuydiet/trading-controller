from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_current_vip_user
from app.models.user import User

router = APIRouter()

# API Thường: Ai login rồi cũng xem được chart
@router.get("/chart-access") 
def check_chart_access(current_user: User = Depends(get_current_user)):
    """
    API này không trả về nến (vì FE tự gọi TradingView),
    nhưng nó xác nhận user ĐƯỢC PHÉP xem biểu đồ.
    """
    return {
        "allow_chart": True,
        "user_tier": current_user.tier,
        "message": f"Xin chào {current_user.email}, bạn được phép truy cập thị trường."
    }

# API VIP: Phải là VIP mới xem được
@router.get("/ai-analysis")
def get_ai_analysis(current_user: User = Depends(get_current_vip_user)):
    return [
        {
            "coin": "BTC/USDT",
            "price": 94500,
            "trend": "bullish",
            "confidence": 89,
            "summary": "Cá voi đang gom hàng mạnh ở vùng giá 93k. RSI cho thấy tín hiệu mua mạnh.",
            "last_updated": "Vừa xong"
        },
        {
            "coin": "ETH/USDT",
            "price": 3200,
            "trend": "bearish",
            "confidence": 75,
            "summary": "Khối lượng giao dịch giảm, cẩn thận bẫy giá (bull trap).",
            "last_updated": "5 phút trước"
        }
    ]