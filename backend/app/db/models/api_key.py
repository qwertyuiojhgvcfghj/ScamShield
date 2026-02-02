"""
api_key.py - API Key document model for database persistence
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime
from enum import Enum
import secrets


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKey(Document):
    """
    API Key document for authenticating programmatic access.
    Stored in database (not in-memory) to persist across restarts.
    """
    user_id: str  # References User._id - indexed
    
    # Key info
    key: str  # The actual API key (hashed prefix visible) - unique indexed
    key_hash: str  # SHA256 hash of the full key for verification
    name: str = "Default API Key"  # User-friendly name
    
    # Status
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    
    # Permissions
    scopes: list[str] = Field(default_factory=lambda: ["scan:read", "scan:write"])
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 1000
    
    # Usage tracking
    last_used_at: Optional[datetime] = None
    total_requests: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # None = never expires
    revoked_at: Optional[datetime] = None
    
    class Settings:
        name = "api_keys"
        
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "key": "sk_live_abc123...xyz789",
                "name": "Production API Key",
                "scopes": ["scan:read", "scan:write"],
                "rate_limit_per_minute": 60
            }
        }
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """
        Generate a new API key and its hash.
        Returns: (visible_key, key_hash)
        """
        import hashlib
        
        # Generate a secure random key
        random_bytes = secrets.token_bytes(32)
        key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison."""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if the API key is valid for use."""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    async def record_usage(self):
        """Record that this API key was used."""
        self.last_used_at = datetime.utcnow()
        self.total_requests += 1
        await self.save()
