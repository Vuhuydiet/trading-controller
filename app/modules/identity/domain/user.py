from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum

class UserTier(str, Enum):
    FREE = "FREE"
    VIP = "VIP"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str
    tier: UserTier = Field(default=UserTier.FREE) 
    is_active: bool = Field(default=True)