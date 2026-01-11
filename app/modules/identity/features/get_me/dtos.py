from pydantic import BaseModel
from typing import Optional
from app.shared.domain.enums import UserTier 

class UserProfileResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    tier: UserTier
    is_active: bool