"""
user.py - User document model
"""

from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum
from beanie import Indexed


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


class User(Document):
    """
    User document for authentication and profile.
    """
    email: Annotated[EmailStr, Indexed(unique=True)]
    password_hash: Optional[str] = None  # Optional for OAuth users
    full_name: str = ""
    phone: Optional[str] = None
    avatar_url: Optional[str] = None  # Profile picture from OAuth
    
    # OAuth fields
    auth_provider: AuthProvider = AuthProvider.LOCAL
    oauth_id: Optional[str] = None  # Google/GitHub user ID
    
    # Account status
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False  # Email verified
    is_phone_verified: bool = False  # Phone verified
    
    # Email verification
    verification_token: Optional[str] = None
    verification_token_expires: Optional[datetime] = None
    
    # Phone verification (OTP)
    phone_otp: Optional[str] = None
    phone_otp_expires: Optional[datetime] = None
    phone_otp_attempts: int = 0  # Track failed attempts
    
    # Password reset
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
        
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone": "+919876543210",
                "role": "user",
                "auth_provider": "local"
            }
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
        
    async def soft_delete(self):
        """Soft delete user by deactivating"""
        self.is_active = False
        self.update_timestamp()
        await self.save()
