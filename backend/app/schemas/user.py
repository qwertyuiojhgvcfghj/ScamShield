"""
user.py - User schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    """Schema for user profile response"""
    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    is_verified: bool
    is_phone_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "john@example.com",
                "full_name": "John Doe",
                "phone": "+919876543210",
                "role": "user",
                "is_verified": True,
                "is_phone_verified": False,
                "created_at": "2026-01-15T10:30:00Z",
                "last_login": "2026-02-01T08:00:00Z"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Smith",
                "phone": "+919876543210"
            }
        }


class UserSettingsResponse(BaseModel):
    """Schema for user settings response"""
    email_alerts: bool
    sms_alerts: bool
    push_notifications: bool
    auto_block: bool
    sensitivity: str  # low, medium, high
    language: str
    timezone: str
    weekly_report: bool
    instant_alerts: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_alerts": True,
                "sms_alerts": False,
                "push_notifications": True,
                "auto_block": True,
                "sensitivity": "medium",
                "language": "en",
                "timezone": "Asia/Kolkata",
                "weekly_report": True,
                "instant_alerts": True
            }
        }


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings"""
    email_alerts: Optional[bool] = None
    sms_alerts: Optional[bool] = None
    push_notifications: Optional[bool] = None
    auto_block: Optional[bool] = None
    sensitivity: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    weekly_report: Optional[bool] = None
    instant_alerts: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_alerts": True,
                "auto_block": True,
                "sensitivity": "high"
            }
        }


class UserStatsResponse(BaseModel):
    """Schema for user statistics"""
    total_scans: int
    scams_detected: int
    scams_blocked: int
    false_positives_reported: int
    member_since: datetime
    current_plan: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scans": 150,
                "scams_detected": 23,
                "scams_blocked": 21,
                "false_positives_reported": 2,
                "member_since": "2026-01-15T10:30:00Z",
                "current_plan": "pro"
            }
        }
