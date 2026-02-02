"""
subscription.py - Subscription and Plan documents
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from enum import Enum


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class Plan(Document):
    """
    Available subscription plans.
    """
    name: str  # Free, Pro, Enterprise
    tier: PlanTier
    
    # Pricing
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    currency: str = "INR"
    
    # Limits
    scan_limit_daily: Optional[int] = None  # None = unlimited
    scan_limit_monthly: Optional[int] = None
    history_retention_days: int = 30
    
    # Features
    features: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    
    class Settings:
        name = "plans"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Pro",
                "tier": "pro",
                "price_monthly": 299.0,
                "price_yearly": 2999.0,
                "scan_limit_daily": 1000,
                "features": ["Unlimited scans", "Priority support", "API access"]
            }
        }


class Subscription(Document):
    """
    User subscription to a plan.
    """
    user_id: Annotated[str, Indexed()]
    plan_id: str  # References Plan._id
    plan_tier: PlanTier  # Denormalized for quick access
    
    # Status
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Dates
    starts_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Payment info (basic - extend for real payment integration)
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None
    
    # Usage tracking
    scans_today: int = 0
    scans_this_month: int = 0
    last_scan_date: Optional[datetime] = None
    
    class Settings:
        name = "subscriptions"
        
    def is_valid(self) -> bool:
        """Check if subscription is currently valid"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    async def increment_scan_count(self):
        """Increment scan counters"""
        today = datetime.utcnow().date()
        
        # Reset daily count if new day
        if self.last_scan_date and self.last_scan_date.date() != today:
            self.scans_today = 0
            
        # Reset monthly count if new month
        if self.last_scan_date:
            if self.last_scan_date.month != datetime.utcnow().month:
                self.scans_this_month = 0
        
        self.scans_today += 1
        self.scans_this_month += 1
        self.last_scan_date = datetime.utcnow()
        await self.save()
