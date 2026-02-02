"""
users.py - User management routes
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
    UserStatsResponse,
)
from app.services.user_service import UserService
from app.services.api_key_service import api_key_service
from app.core.dependencies import get_current_user, get_current_active_user
from app.db.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


# ==========================================
# API KEY MANAGEMENT (Database-backed)
# ==========================================


class APIKeyCreateRequest(BaseModel):
    """Request to create a new API key"""
    name: str = Field("Default API Key", max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    scopes: Optional[List[str]] = ["scan:read", "scan:write"]


class APIKeyResponse(BaseModel):
    """Schema for API key response (includes raw key - only on creation)"""
    id: str
    api_key: str  # Full key - only shown once!
    name: str
    prefix: str
    created_at: str
    expires_at: Optional[str] = None
    status: str = "active"
    
    
class APIKeyInfo(BaseModel):
    """Schema for API key info (without full key)"""
    id: str
    name: str
    prefix: str
    created_at: str
    expires_at: Optional[str] = None
    status: str
    last_used: Optional[str] = None
    total_requests: int = 0
    scopes: List[str] = []


@router.post(
    "/me/api-keys",
    response_model=APIKeyResponse,
    summary="Generate new API key"
)
async def generate_user_api_key(
    request: APIKeyCreateRequest = APIKeyCreateRequest(),
    user: User = Depends(get_current_active_user)
):
    """
    Generate a new API key for the current user.
    
    **Warning**: The API key is only shown once - save it securely!
    
    You can have multiple API keys for different purposes.
    """
    user_id = str(user.id)
    
    # Create new key in database
    api_key_doc, raw_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days
    )
    
    return APIKeyResponse(
        id=str(api_key_doc.id),
        api_key=raw_key,  # Full key - only time it's shown!
        name=api_key_doc.name,
        prefix=api_key_doc.key,
        created_at=api_key_doc.created_at.isoformat(),
        expires_at=api_key_doc.expires_at.isoformat() if api_key_doc.expires_at else None,
        status=api_key_doc.status.value
    )


@router.get(
    "/me/api-keys",
    response_model=List[APIKeyInfo],
    summary="List all API keys"
)
async def list_user_api_keys(user: User = Depends(get_current_active_user)):
    """
    Get all API keys for the current user.
    
    **Note**: Full API keys are never returned - only metadata.
    """
    user_id = str(user.id)
    
    keys = await api_key_service.get_user_api_keys(user_id)
    
    return [
        APIKeyInfo(
            id=str(key.id),
            name=key.name,
            prefix=key.key,
            created_at=key.created_at.isoformat(),
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            status=key.status.value,
            last_used=key.last_used_at.isoformat() if key.last_used_at else None,
            total_requests=key.total_requests,
            scopes=key.scopes
        )
        for key in keys
    ]


@router.get(
    "/me/api-keys/{key_id}",
    response_model=APIKeyInfo,
    summary="Get API key info"
)
async def get_user_api_key_info(
    key_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Get information about a specific API key.
    """
    user_id = str(user.id)
    
    key = await api_key_service.get_api_key_by_id(key_id, user_id)
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyInfo(
        id=str(key.id),
        name=key.name,
        prefix=key.key,
        created_at=key.created_at.isoformat(),
        expires_at=key.expires_at.isoformat() if key.expires_at else None,
        status=key.status.value,
        last_used=key.last_used_at.isoformat() if key.last_used_at else None,
        total_requests=key.total_requests,
        scopes=key.scopes
    )


@router.delete(
    "/me/api-keys/{key_id}",
    summary="Revoke API key"
)
async def revoke_user_api_key(
    key_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Revoke an API key. The key will immediately stop working.
    """
    user_id = str(user.id)
    
    success = await api_key_service.revoke_api_key(key_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {
        "status": "success",
        "message": "API key revoked successfully"
    }


# Legacy endpoint for backward compatibility
@router.post("/me/api-key", response_model=APIKeyResponse, include_in_schema=False)
async def generate_user_api_key_legacy(user: User = Depends(get_current_active_user)):
    """Legacy endpoint - creates a default API key"""
    return await generate_user_api_key(APIKeyCreateRequest(), user)


@router.get("/me/api-key", response_model=APIKeyInfo, include_in_schema=False)
async def get_user_api_key_info_legacy(user: User = Depends(get_current_active_user)):
    """Legacy endpoint - returns first active API key"""
    keys = await api_key_service.get_active_api_keys(str(user.id))
    if not keys:
        raise HTTPException(status_code=404, detail="No API key found")
    key = keys[0]
    return APIKeyInfo(
        id=str(key.id),
        name=key.name,
        prefix=key.key,
        created_at=key.created_at.isoformat(),
        expires_at=key.expires_at.isoformat() if key.expires_at else None,
        status=key.status.value,
        last_used=key.last_used_at.isoformat() if key.last_used_at else None,
        total_requests=key.total_requests,
        scopes=key.scopes
    )


@router.delete("/me/api-key", include_in_schema=False)
async def revoke_user_api_key_legacy(user: User = Depends(get_current_active_user)):
    """Legacy endpoint - revokes first active API key"""
    keys = await api_key_service.get_active_api_keys(str(user.id))
    if not keys:
        raise HTTPException(status_code=404, detail="No API key found")
    await api_key_service.revoke_api_key(str(keys[0].id), str(user.id))
    return {"status": "success", "message": "API key revoked"}


# ==========================================
# USER PROFILE ENDPOINTS
# ==========================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_profile(user: User = Depends(get_current_active_user)):
    """
    Get the current user's profile information.
    """
    return await UserService.get_user_profile(user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_active_user)
):
    """
    Update the current user's profile.
    
    - **full_name**: New display name
    - **phone**: New phone number
    """
    return await UserService.update_user_profile(user, data)


@router.get(
    "/me/settings",
    response_model=UserSettingsResponse,
    summary="Get user settings"
)
async def get_settings(user: User = Depends(get_current_active_user)):
    """
    Get the current user's settings and preferences.
    """
    return await UserService.get_user_settings(str(user.id))


@router.put(
    "/me/settings",
    response_model=UserSettingsResponse,
    summary="Update user settings"
)
async def update_settings(
    data: UserSettingsUpdate,
    user: User = Depends(get_current_active_user)
):
    """
    Update the current user's settings.
    
    - **email_alerts**: Enable email notifications
    - **sms_alerts**: Enable SMS notifications
    - **auto_block**: Automatically block detected scams
    - **sensitivity**: Detection sensitivity (low/medium/high)
    """
    return await UserService.update_user_settings(str(user.id), data)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get user statistics"
)
async def get_stats(user: User = Depends(get_current_active_user)):
    """
    Get the current user's usage statistics.
    """
    return await UserService.get_user_stats(str(user.id))


@router.delete(
    "/me",
    summary="Delete user account"
)
async def delete_account(user: User = Depends(get_current_active_user)):
    """
    Delete (deactivate) the current user's account.
    This is a soft delete - the account can be recovered.
    """
    await UserService.delete_user_account(user)
    
    return {
        "status": "success",
        "message": "Account deactivated successfully"
    }
