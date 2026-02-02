"""
api_key_service.py - Service for managing API keys with database persistence
"""

from typing import Optional, List
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.db.models.api_key import APIKey, APIKeyStatus
from app.db.models.user import User


class APIKeyService:
    """Service for managing API keys."""
    
    @staticmethod
    async def create_api_key(
        user_id: str,
        name: str = "Default API Key",
        scopes: List[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 1000
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Returns:
            tuple: (APIKey document, raw_key)
            The raw_key is only returned once and should be shown to the user.
        """
        # Generate the key
        raw_key, key_hash = APIKey.generate_key()
        
        # Create visible prefix (for display)
        visible_key = f"{raw_key[:12]}...{raw_key[-4:]}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create the API key document
        api_key = APIKey(
            user_id=user_id,
            key=visible_key,  # Store only the visible prefix
            key_hash=key_hash,
            name=name,
            scopes=scopes or ["scan:read", "scan:write"],
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_day=rate_limit_per_day,
            expires_at=expires_at
        )
        
        await api_key.insert()
        
        # Return both the document and the raw key (only time it's available)
        return api_key, raw_key
    
    @staticmethod
    async def validate_api_key(raw_key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the associated document.
        
        Returns:
            APIKey if valid, None otherwise
        """
        # Hash the provided key
        key_hash = APIKey.hash_key(raw_key)
        
        # Find the key by hash
        api_key = await APIKey.find_one(APIKey.key_hash == key_hash)
        
        if not api_key:
            return None
        
        if not api_key.is_valid():
            return None
        
        # Record usage
        await api_key.record_usage()
        
        return api_key
    
    @staticmethod
    async def get_user_api_keys(user_id: str) -> List[APIKey]:
        """Get all API keys for a user."""
        return await APIKey.find(APIKey.user_id == user_id).to_list()
    
    @staticmethod
    async def get_active_api_keys(user_id: str) -> List[APIKey]:
        """Get all active API keys for a user."""
        return await APIKey.find(
            APIKey.user_id == user_id,
            APIKey.status == APIKeyStatus.ACTIVE
        ).to_list()
    
    @staticmethod
    async def revoke_api_key(key_id: str, user_id: str) -> bool:
        """
        Revoke an API key.
        
        Returns:
            True if revoked, False if not found or not owned by user
        """
        api_key = await APIKey.find_one(
            APIKey.id == PydanticObjectId(key_id),
            APIKey.user_id == user_id
        )
        
        if not api_key:
            return False
        
        api_key.status = APIKeyStatus.REVOKED
        api_key.revoked_at = datetime.utcnow()
        await api_key.save()
        
        return True
    
    @staticmethod
    async def delete_api_key(key_id: str, user_id: str) -> bool:
        """
        Delete an API key permanently.
        
        Returns:
            True if deleted, False if not found or not owned by user
        """
        api_key = await APIKey.find_one(
            APIKey.id == PydanticObjectId(key_id),
            APIKey.user_id == user_id
        )
        
        if not api_key:
            return False
        
        await api_key.delete()
        return True
    
    @staticmethod
    async def update_api_key(
        key_id: str,
        user_id: str,
        name: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        rate_limit_per_minute: Optional[int] = None,
        rate_limit_per_day: Optional[int] = None
    ) -> Optional[APIKey]:
        """Update an API key's settings."""
        api_key = await APIKey.find_one(
            APIKey.id == PydanticObjectId(key_id),
            APIKey.user_id == user_id
        )
        
        if not api_key:
            return None
        
        if name is not None:
            api_key.name = name
        if scopes is not None:
            api_key.scopes = scopes
        if rate_limit_per_minute is not None:
            api_key.rate_limit_per_minute = rate_limit_per_minute
        if rate_limit_per_day is not None:
            api_key.rate_limit_per_day = rate_limit_per_day
        
        await api_key.save()
        return api_key
    
    @staticmethod
    async def get_api_key_by_id(key_id: str, user_id: str) -> Optional[APIKey]:
        """Get a specific API key by ID."""
        return await APIKey.find_one(
            APIKey.id == PydanticObjectId(key_id),
            APIKey.user_id == user_id
        )
    
    @staticmethod
    async def cleanup_expired_keys():
        """Mark expired API keys as expired (for scheduled task)."""
        now = datetime.utcnow()
        expired_keys = await APIKey.find(
            APIKey.status == APIKeyStatus.ACTIVE,
            APIKey.expires_at != None,
            APIKey.expires_at < now
        ).to_list()
        
        for key in expired_keys:
            key.status = APIKeyStatus.EXPIRED
            await key.save()
        
        return len(expired_keys)


# Singleton instance
api_key_service = APIKeyService()
