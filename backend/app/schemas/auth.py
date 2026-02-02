"""
auth.py - Authentication schemas
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

from app.core.validators import (
    PasswordValidator,
    EmailValidator,
    PhoneValidator,
    validate_password_strength
)


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength using PasswordValidator."""
        is_valid, errors = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(errors[0])  # Return first error
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email_not_disposable(cls, v):
        """Reject disposable email addresses."""
        if EmailValidator.is_disposable(v):
            raise ValueError("Disposable email addresses are not allowed")
        return v.lower()
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Validate and normalize phone number."""
        if v:
            is_valid, error = PhoneValidator.validate_indian(v)
            if not is_valid:
                raise ValueError(error)
            return PhoneValidator.normalize(v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePass@123",
                "full_name": "John Doe",
                "phone": "+919876543210"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePass123"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload"""
    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str  # "access" or "refresh"


class RefreshToken(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456...",
                "new_password": "NewSecurePass123"
            }
        }


class ChangePassword(BaseModel):
    """Schema for changing password (when logged in)"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class VerifyEmail(BaseModel):
    """Schema for email verification"""
    token: str


class ResendVerificationEmail(BaseModel):
    """Schema for resending verification email"""
    email: EmailStr


class SendPhoneOTP(BaseModel):
    """Schema for sending phone OTP"""
    phone: str = Field(..., min_length=10, max_length=15)
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        # Remove any spaces or dashes
        v = re.sub(r'[\s\-]', '', v)
        # Check if it's a valid phone number
        if not re.match(r'^\+?[1-9]\d{9,14}$', v):
            raise ValueError("Invalid phone number format")
        return v


class VerifyPhoneOTP(BaseModel):
    """Schema for verifying phone OTP"""
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6)
    
    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        """Validate OTP format."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class VerificationStatus(BaseModel):
    """Schema for verification status response"""
    email_verified: bool
    phone_verified: bool
    email: str
    phone: Optional[str] = None


# ============================================================
# OAUTH SCHEMAS
# ============================================================

class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth callback with authorization code"""
    code: str
    redirect_uri: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "4/0AX4XfWj...",
                "redirect_uri": "http://localhost:5500/login.html"
            }
        }


class GoogleTokenRequest(BaseModel):
    """Schema for Google OAuth with ID token (frontend flow)"""
    id_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class GitHubAuthRequest(BaseModel):
    """Schema for GitHub OAuth callback"""
    code: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "abc123def456..."
            }
        }


class OAuthUserInfo(BaseModel):
    """Schema for OAuth user info"""
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    oauth_id: str
    provider: str  # "google" or "github"
