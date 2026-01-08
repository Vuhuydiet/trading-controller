from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Optional
from app.shared.core.config import settings
from app.modules.identity.public_api import UserDTO

# OAuth2 scheme that doesn't raise error if token is missing
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/v1/login", auto_error=False)


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional)) -> Optional[UserDTO]:
    """
    Optional authentication dependency.

    Returns:
        - UserDTO if valid token provided
        - None if no token or invalid token

    Use this for public endpoints that can optionally use auth for premium features.

    Example:
        @router.get("/public-endpoint")
        async def public_endpoint(user: Optional[UserDTO] = Depends(get_current_user_optional)):
            if user:
                # User is logged in, provide premium features
                max_limit = 1000 if user.tier in ["premium", "vip"] else 500
            else:
                # Anonymous user, provide basic features
                max_limit = 500
    """
    if token is None:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        tier: str = payload.get("tier", "free")
        email: str = payload.get("email", "from_token")

        if user_id is None:
            return None

        return UserDTO(id=int(user_id), email=email, tier=tier)
    except JWTError:
        return None
    except Exception:
        return None


def get_user_limits(user: Optional[UserDTO]) -> dict:
    """
    Get rate limits and feature access based on user tier.

    Args:
        user: Optional UserDTO from authentication

    Returns:
        dict with limits:
            - max_klines: Maximum number of candlesticks
            - max_depth: Maximum order book depth
            - rate_limit: Requests per minute
            - has_ai_access: Can use AI features
    """
    if user is None:
        # Anonymous user - most restricted
        return {
            "max_klines": 500,
            "max_depth": 100,
            "rate_limit": 5,  # requests per minute
            "has_ai_access": False,
            "tier": "anonymous"
        }

    # Tier-based limits
    tier_limits = {
        "free": {
            "max_klines": 500,
            "max_depth": 100,
            "rate_limit": 10,
            "has_ai_access": False,
            "tier": "free"
        },
        "vip": {
            "max_klines": 5000,
            "max_depth": 1000,
            "rate_limit": 1000,
            "has_ai_access": True,
            "tier": "vip"
        }
    }

    return tier_limits.get(user.tier, tier_limits["free"])
