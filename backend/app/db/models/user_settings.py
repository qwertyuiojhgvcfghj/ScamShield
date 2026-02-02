"""
user_settings.py - User settings/preferences document
"""

from beanie import Document, Indexed, Link
from pydantic import Field
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserSettings(Document):
    """
    User preferences and notification settings.
    One-to-one relationship with User.
    """
    user_id: Annotated[str, Indexed(unique=True)]  # References User._id as string
    
    # Notification preferences
    email_alerts: bool = True
    sms_alerts: bool = False
    push_notifications: bool = True
    
    # Protection settings
    auto_block: bool = True
    sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM
    
    # Display preferences
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    
    # Feature toggles
    weekly_report: bool = True
    instant_alerts: bool = True
    
    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_settings"
        
    @classmethod
    async def get_or_create(cls, user_id: str) -> "UserSettings":
        """Get existing settings or create defaults"""
        settings = await cls.find_one(cls.user_id == user_id)
        if not settings:
            settings = cls(user_id=user_id)
            await settings.insert()
        return settings
