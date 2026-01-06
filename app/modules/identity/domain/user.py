from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum

class UserTier(str, Enum):
    FREE = "FREE"
    VIP = "VIP"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    tier: UserTier = Field(default=UserTier.FREE) # Mặc định là Free
    is_active: bool = Field(default=True)