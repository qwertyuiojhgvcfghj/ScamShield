"""
user_service.py - User management business logic
"""

from datetime import datetime
from typing import Optional

from app.db.models.user import User
from app.db.models.user_settings import UserSettings
from app.db.models.scan import ScanRequest
from app.db.models.subscription import Subscription
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
    UserStatsResponse,
)


class UserService:
    """
    Service for user profile and settings management.
    """
    
    @staticmethod
    async def get_user_profile(user: User) -> UserResponse:
        """
        Get user profile as response schema.
        """
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role.value,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
        )
    
    @staticmethod
    async def update_user_profile(user: User, data: UserUpdate) -> UserResponse:
        """
        Update user profile.
        """
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone is not None:
            user.phone = data.phone
        
        user.update_timestamp()
        await user.save()
        
        return await UserService.get_user_profile(user)
    
    @staticmethod
    async def get_user_settings(user_id: str) -> UserSettingsResponse:
        """
        Get user settings.
        """
        settings = await UserSettings.get_or_create(user_id)
        
        return UserSettingsResponse(
            email_alerts=settings.email_alerts,
            sms_alerts=settings.sms_alerts,
            push_notifications=settings.push_notifications,
            auto_block=settings.auto_block,
            sensitivity=settings.sensitivity.value,
            language=settings.language,
            timezone=settings.timezone,
            weekly_report=settings.weekly_report,
            instant_alerts=settings.instant_alerts,
        )
    
    @staticmethod
    async def update_user_settings(
        user_id: str,
        data: UserSettingsUpdate
    ) -> UserSettingsResponse:
        """
        Update user settings.
        """
        settings = await UserSettings.get_or_create(user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(settings, field) and value is not None:
                setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        await settings.save()
        
        return await UserService.get_user_settings(user_id)
    
    @staticmethod
    async def get_user_stats(user_id: str) -> UserStatsResponse:
        """
        Get user statistics.
        """
        # Get user
        user = await User.get(user_id)
        
        # Count scans
        total_scans = await ScanRequest.find(
            ScanRequest.user_id == user_id
        ).count()
        
        scams_detected = await ScanRequest.find(
            ScanRequest.user_id == user_id,
            ScanRequest.is_scam == True
        ).count()
        
        scams_blocked = await ScanRequest.find(
            ScanRequest.user_id == user_id,
            ScanRequest.is_scam == True,
            ScanRequest.auto_blocked == True
        ).count()
        
        false_positives = await ScanRequest.find(
            ScanRequest.user_id == user_id,
            ScanRequest.user_feedback == "false_positive"
        ).count()
        
        # Get subscription
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        plan = subscription.plan_tier.value if subscription else "free"
        
        return UserStatsResponse(
            total_scans=total_scans,
            scams_detected=scams_detected,
            scams_blocked=scams_blocked,
            false_positives_reported=false_positives,
            member_since=user.created_at,
            current_plan=plan,
        )
    
    @staticmethod
    async def delete_user_account(user: User):
        """
        Soft delete user account.
        """
        await user.soft_delete()
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email.
        """
        return await User.find_one(User.email == email.lower())
