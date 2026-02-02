"""
subscription.py - Subscription and plan schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlanFeature(BaseModel):
    """Schema for plan feature"""
    name: str
    included: bool
    limit: Optional[str] = None


class PlanResponse(BaseModel):
    """Schema for plan details"""
    id: str
    name: str
    tier: str  # free, pro, enterprise
    price_monthly: float
    price_yearly: float
    currency: str
    scan_limit_daily: Optional[int] = None
    scan_limit_monthly: Optional[int] = None
    features: List[str]
    is_popular: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Pro",
                "tier": "pro",
                "price_monthly": 299.0,
                "price_yearly": 2999.0,
                "currency": "INR",
                "scan_limit_daily": 1000,
                "scan_limit_monthly": None,
                "features": [
                    "1000 scans/day",
                    "Priority support",
                    "API access",
                    "Advanced analytics",
                    "Email protection",
                    "SMS protection"
                ],
                "is_popular": True
            }
        }


class PlanListResponse(BaseModel):
    """Schema for plan list"""
    plans: List[PlanResponse]


class SubscriptionResponse(BaseModel):
    """Schema for user's subscription"""
    id: str
    plan_name: str
    plan_tier: str
    status: str  # active, cancelled, expired, trial
    starts_at: datetime
    expires_at: Optional[datetime] = None
    
    # Usage
    scans_today: int
    scans_this_month: int
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    
    # Billing (if applicable)
    next_billing_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "plan_name": "Pro",
                "plan_tier": "pro",
                "status": "active",
                "starts_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-02-01T00:00:00Z",
                "scans_today": 45,
                "scans_this_month": 892,
                "daily_limit": 1000,
                "monthly_limit": None
            }
        }


class SubscribeRequest(BaseModel):
    """Schema for subscribing to a plan"""
    plan_id: str
    billing_period: str = Field(..., pattern="^(monthly|yearly)$")
    payment_method: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "507f1f77bcf86cd799439011",
                "billing_period": "monthly",
                "payment_method": "card"
            }
        }


class SubscriptionCancel(BaseModel):
    """Schema for cancellation request"""
    reason: Optional[str] = Field(None, max_length=500)
    feedback: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Too expensive",
                "feedback": "Great service but need to cut costs"
            }
        }
