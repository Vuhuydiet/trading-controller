from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from app.shared.core.config import settings # Đảm bảo import đúng config

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