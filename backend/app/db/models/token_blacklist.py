"""
token_blacklist.py - Blacklisted JWT tokens for logout
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Annotated
from datetime import datetime


class TokenBlacklist(Document):
    """
    Blacklisted tokens (for logout functionality).
    Tokens are stored until their expiry time.
    """
    token: Annotated[str, Indexed(unique=True)]
    expires_at: datetime
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "token_blacklist"
        
    @classmethod
    async def is_blacklisted(cls, token: str) -> bool:
        """Check if a token is blacklisted"""
        entry = await cls.find_one(cls.token == token)
        return entry is not None
    
    @classmethod
    async def add_to_blacklist(cls, token: str, expires_at: datetime):
        """Add a token to blacklist"""
        entry = cls(token=token, expires_at=expires_at)
        await entry.insert()
    
    @classmethod
    async def cleanup_expired(cls):
        """Remove expired tokens from blacklist"""
        await cls.find(cls.expires_at < datetime.utcnow()).delete()
