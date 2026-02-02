"""
subscriptions.py - Subscription management routes
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.subscription import (
    PlanResponse,
    PlanListResponse,
    SubscriptionResponse,
    SubscribeRequest,
    SubscriptionCancel,
)
from app.services.subscription_service import SubscriptionService
from app.core.dependencies import get_current_active_user
from app.db.models.user import User


router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get(
    "/plans",
    response_model=PlanListResponse,
    summary="Get available plans"
)
async def get_plans():
    """
    Get all available subscription plans.
    
    Plans include:
    - **Free**: Basic protection with limited scans
    - **Pro**: Advanced protection with more features
    - **Enterprise**: Full protection with unlimited access
    """
    return await SubscriptionService.get_plans()


@router.get(
    "/me",
    response_model=SubscriptionResponse,
    summary="Get current subscription"
)
async def get_subscription(user: User = Depends(get_current_active_user)):
    """
    Get the current user's subscription details.
    
    Includes:
    - Current plan and tier
    - Status (active, cancelled, expired)
    - Usage counts (scans today, scans this month)
    - Expiration date
    """
    result = await SubscriptionService.get_user_subscription(str(user.id))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    return result


@router.post(
    "/subscribe",
    response_model=SubscriptionResponse,
    summary="Subscribe to a plan"
)
async def subscribe(
    data: SubscribeRequest,
    user: User = Depends(get_current_active_user)
):
    """
    Subscribe to a plan or upgrade existing subscription.
    
    - **plan_id**: The ID of the plan to subscribe to
    - **billing_period**: "monthly" or "yearly"
    - **payment_method**: Payment method (optional for now)
    
    Note: Payment integration would go here in production.
    """
    try:
        return await SubscriptionService.create_subscription(str(user.id), data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/cancel",
    summary="Cancel subscription"
)
async def cancel_subscription(
    data: SubscriptionCancel = None,
    user: User = Depends(get_current_active_user)
):
    """
    Cancel current subscription.
    
    The subscription will remain active until the end of the billing period,
    then revert to the free plan.
    
    - **reason**: Why are you cancelling? (optional)
    - **feedback**: Any additional feedback (optional)
    """
    reason = data.reason if data else None
    success = await SubscriptionService.cancel_subscription(str(user.id), reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription to cancel"
        )
    
    return {
        "status": "success",
        "message": "Subscription cancelled. You will be moved to the free plan."
    }


@router.get(
    "/usage",
    summary="Get usage stats"
)
async def get_usage(user: User = Depends(get_current_active_user)):
    """
    Get current usage statistics.
    
    Shows how many scans have been used vs. limits.
    """
    subscription = await SubscriptionService.get_user_subscription(str(user.id))
    
    if not subscription:
        return {
            "plan": "free",
            "scans_today": 0,
            "daily_limit": 10,
            "scans_remaining": 10,
        }
    
    remaining = None
    if subscription.daily_limit:
        remaining = max(0, subscription.daily_limit - subscription.scans_today)
    
    return {
        "plan": subscription.plan_tier,
        "scans_today": subscription.scans_today,
        "daily_limit": subscription.daily_limit,
        "scans_remaining": remaining,
        "scans_this_month": subscription.scans_this_month,
        "monthly_limit": subscription.monthly_limit,
    }
