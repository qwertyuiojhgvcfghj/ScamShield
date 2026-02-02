"""
dependencies.py - FastAPI dependencies for auth and permissions
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security import decode_token
from app.db.models.user import User, UserRole
from app.db.models.subscription import Subscription, PlanTier
from app.db.models.token_blacklist import TokenBlacklist


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"email": user.email}
    """
    token = credentials.credentials
    
    # Check if token is blacklisted
    if await TokenBlacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return user


async def get_current_verified_user(
    user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure user is verified.
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    return user


async def get_current_admin(
    user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure user has admin role.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


class RequireSubscription:
    """
    Dependency class to check if user has required subscription tier.
    
    Usage:
        @app.get("/pro-feature")
        async def pro_feature(
            user: User = Depends(RequireSubscription(PlanTier.PRO))
        ):
            return {"message": "Welcome, Pro user!"}
    """
    
    def __init__(self, min_tier: PlanTier = PlanTier.FREE):
        self.min_tier = min_tier
        self.tier_levels = {
            PlanTier.FREE: 0,
            PlanTier.PRO: 1,
            PlanTier.ENTERPRISE: 2,
        }
    
    async def __call__(
        self,
        user: User = Depends(get_current_active_user)
    ) -> User:
        # Get user's subscription
        subscription = await Subscription.find_one(
            Subscription.user_id == str(user.id),
            Subscription.status == "active"
        )
        
        if not subscription:
            # No subscription = free tier
            user_tier = PlanTier.FREE
        else:
            user_tier = subscription.plan_tier
        
        # Check tier level
        user_level = self.tier_levels.get(user_tier, 0)
        required_level = self.tier_levels.get(self.min_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {self.min_tier.value} subscription or higher"
            )
        
        return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    Dependency to optionally get user (for endpoints that work with or without auth).
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        if await TokenBlacklist.is_blacklisted(token):
            return None
        
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await User.get(user_id)
    except Exception:
        return None
