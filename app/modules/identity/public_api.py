from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from app.shared.core.config import settings # Đảm bảo import đúng config
from sqlmodel import Session, select
from app.modules.identity.domain.user import User
from app.shared.domain.enums import UserTier

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

# DTO này để share cho các module khác, tránh lộ User Model gốc
class UserDTO(BaseModel):
    id: int
    email: str
    tier: str

def get_current_user_dto(token: str = Depends(oauth2_scheme)) -> UserDTO:
    """
    Hàm này thay thế cho get_current_user cũ trong deps.py.
    Nó giải mã token và trả về thông tin cơ bản.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        tier: str = payload.get("tier") # Lấy tier từ token luôn cho nhanh
        if user_id is None:
            raise credentials_exception
        
        # Ở đây ta trust thông tin trong Token để giảm query DB. 
        # Nếu cần chính xác tuyệt đối, bạn có thể inject Session và query DB.
        return UserDTO(id=int(user_id), email="from_token", tier=tier)
        
    except JWTError:
        raise credentials_exception


def upgrade_user_to_vip(session: Session, user_id: int):
    user = session.get(User, user_id)
    if user:
        user.tier = "VIP"
        session.add(user)
        session.commit()
        session.refresh(user)
        return True
    return False

def set_user_tier(session: Session, user_id: int, new_tier: UserTier) -> bool:
    """
    Hàm này cho phép các module khác yêu cầu cập nhật Tier của user.
    Subscription không cần biết User table trông như thế nào.
    """
    user = session.get(User, user_id)
    if not user:
        return False

    user.tier = new_tier
    session.add(user)
    # Lưu ý: Ta không commit ở đây mà để Handler bên ngoài commit 
    # để đảm bảo tính transaction (Atomic) nếu handler có làm nhiều việc khác.
    return True