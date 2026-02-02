"""
subscription_service.py - Subscription management business logic
"""

from datetime import datetime, timedelta
from typing import Optional, List

from app.db.models.subscription import Subscription, Plan, PlanTier, SubscriptionStatus
from app.schemas.subscription import (
    PlanResponse,
    PlanListResponse,
    SubscriptionResponse,
    SubscribeRequest,
)


class SubscriptionService:
    """
    Service for subscription and plan management.
    """
    
    @staticmethod
    async def initialize_default_plans():
        """
        Create default plans if they don't exist.
        Call this on app startup.
        """
        plans = [
            {
                "name": "Free",
                "tier": PlanTier.FREE,
                "price_monthly": 0,
                "price_yearly": 0,
                "scan_limit_daily": 10,
                "scan_limit_monthly": 100,
                "history_retention_days": 7,
                "features": [
                    "10 scans per day",
                    "Basic scam detection",
                    "7-day history",
                    "Email alerts"
                ],
            },
            {
                "name": "Pro",
                "tier": PlanTier.PRO,
                "price_monthly": 299,
                "price_yearly": 2999,
                "scan_limit_daily": 1000,
                "scan_limit_monthly": None,
                "history_retention_days": 90,
                "features": [
                    "1000 scans per day",
                    "Advanced AI detection",
                    "90-day history",
                    "Priority support",
                    "API access",
                    "SMS & Email protection",
                    "Weekly reports"
                ],
            },
            {
                "name": "Enterprise",
                "tier": PlanTier.ENTERPRISE,
                "price_monthly": 999,
                "price_yearly": 9999,
                "scan_limit_daily": None,
                "scan_limit_monthly": None,
                "history_retention_days": 365,
                "features": [
                    "Unlimited scans",
                    "Premium AI detection",
                    "1-year history",
                    "24/7 dedicated support",
                    "Full API access",
                    "Custom integrations",
                    "Team management",
                    "White-label option",
                    "SLA guarantee"
                ],
            },
        ]
        
        for plan_data in plans:
            existing = await Plan.find_one(Plan.tier == plan_data["tier"])
            if not existing:
                plan = Plan(**plan_data)
                await plan.insert()
    
    @staticmethod
    async def get_plans() -> PlanListResponse:
        """
        Get all available plans.
        """
        plans = await Plan.find(Plan.is_active == True).to_list()
        
        plan_responses = []
        for plan in plans:
            plan_responses.append(
                PlanResponse(
                    id=str(plan.id),
                    name=plan.name,
                    tier=plan.tier.value,
                    price_monthly=plan.price_monthly,
                    price_yearly=plan.price_yearly,
                    currency=plan.currency,
                    scan_limit_daily=plan.scan_limit_daily,
                    scan_limit_monthly=plan.scan_limit_monthly,
                    features=plan.features,
                    is_popular=plan.tier == PlanTier.PRO,
                )
            )
        
        return PlanListResponse(plans=plan_responses)
    
    @staticmethod
    async def get_user_subscription(user_id: str) -> Optional[SubscriptionResponse]:
        """
        Get user's current subscription.
        """
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if not subscription:
            return None
        
        # Get plan details
        plan = await Plan.find_one(Plan.tier == subscription.plan_tier)
        
        return SubscriptionResponse(
            id=str(subscription.id),
            plan_name=plan.name if plan else subscription.plan_tier.value,
            plan_tier=subscription.plan_tier.value,
            status=subscription.status.value,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
            scans_today=subscription.scans_today,
            scans_this_month=subscription.scans_this_month,
            daily_limit=plan.scan_limit_daily if plan else None,
            monthly_limit=plan.scan_limit_monthly if plan else None,
        )
    
    @staticmethod
    async def create_subscription(
        user_id: str,
        data: SubscribeRequest
    ) -> SubscriptionResponse:
        """
        Create or upgrade subscription.
        """
        # Get plan
        plan = await Plan.get(data.plan_id)
        if not plan:
            raise ValueError("Invalid plan ID")
        
        # Calculate expiry
        if data.billing_period == "yearly":
            expires_at = datetime.utcnow() + timedelta(days=365)
        else:
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Check existing subscription
        existing = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if existing:
            # Update existing
            existing.plan_id = data.plan_id
            existing.plan_tier = plan.tier
            existing.status = SubscriptionStatus.ACTIVE
            existing.starts_at = datetime.utcnow()
            existing.expires_at = expires_at
            existing.payment_method = data.payment_method
            await existing.save()
            subscription = existing
        else:
            # Create new
            subscription = Subscription(
                user_id=user_id,
                plan_id=data.plan_id,
                plan_tier=plan.tier,
                status=SubscriptionStatus.ACTIVE,
                expires_at=expires_at,
                payment_method=data.payment_method,
            )
            await subscription.insert()
        
        return SubscriptionResponse(
            id=str(subscription.id),
            plan_name=plan.name,
            plan_tier=subscription.plan_tier.value,
            status=subscription.status.value,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
            scans_today=subscription.scans_today,
            scans_this_month=subscription.scans_this_month,
            daily_limit=plan.scan_limit_daily,
            monthly_limit=plan.scan_limit_monthly,
        )
    
    @staticmethod
    async def cancel_subscription(
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Cancel user's subscription.
        """
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        await subscription.save()
        
        # Create free subscription
        free_plan = await Plan.find_one(Plan.tier == PlanTier.FREE)
        
        new_subscription = Subscription(
            user_id=user_id,
            plan_id=str(free_plan.id) if free_plan else "free",
            plan_tier=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
        await new_subscription.insert()
        
        return True
    
    @staticmethod
    async def check_can_scan(user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can perform a scan.
        
        Returns:
            (can_scan, error_message)
        """
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if not subscription:
            return True, None  # No subscription = free tier
        
        plan = await Plan.find_one(Plan.tier == subscription.plan_tier)
        
        if not plan:
            return True, None
        
        # Check daily limit
        if plan.scan_limit_daily is not None:
            if subscription.scans_today >= plan.scan_limit_daily:
                return False, f"Daily scan limit ({plan.scan_limit_daily}) reached. Upgrade for more scans."
        
        # Check monthly limit
        if plan.scan_limit_monthly is not None:
            if subscription.scans_this_month >= plan.scan_limit_monthly:
                return False, f"Monthly scan limit ({plan.scan_limit_monthly}) reached. Upgrade for more scans."
        
        return True, None
