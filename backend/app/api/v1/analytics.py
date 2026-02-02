"""
analytics.py - Analytics and dashboard routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.schemas.analytics import (
    DashboardStats,
    TrendData,
    ScamTypeAnalytics,
    GlobalStats,
)
from app.services.analytics_service import AnalyticsService
from app.core.dependencies import get_current_active_user, get_optional_user
from app.db.models.user import User


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Get dashboard statistics"
)
async def get_dashboard_stats(user: User = Depends(get_current_active_user)):
    """
    Get statistics for the user's dashboard.
    
    Includes:
    - Total scans, scams detected, scams blocked
    - Protection rate
    - Today's and this month's stats
    - Active threats count
    - Scam trend (vs last period)
    - Current plan and remaining scans
    """
    return await AnalyticsService.get_dashboard_stats(str(user.id))


@router.get(
    "/trends",
    response_model=TrendData,
    summary="Get scam trends"
)
async def get_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    user: User = Depends(get_current_active_user)
):
    """
    Get scam detection trends over time.
    
    - **days**: Number of days to analyze (7-365)
    
    Returns daily data points with:
    - Number of scans
    - Scams detected
    - Scams blocked
    """
    return await AnalyticsService.get_trends(str(user.id), days)


@router.get(
    "/breakdown",
    response_model=ScamTypeAnalytics,
    summary="Get scam type breakdown"
)
async def get_breakdown(user: User = Depends(get_current_active_user)):
    """
    Get breakdown of detected scams by type.
    
    Returns:
    - List of scam types with counts and percentages
    - Most common scam type
    - Fastest growing scam type
    """
    return await AnalyticsService.get_scam_type_breakdown(str(user.id))


@router.get(
    "/global",
    response_model=GlobalStats,
    summary="Get global statistics (public)"
)
async def get_global_stats():
    """
    Get global/public statistics for the homepage.
    
    This endpoint is public (no auth required).
    
    Returns:
    - Total scams blocked globally
    - Total users protected
    - Detection accuracy
    - Average response time
    """
    return await AnalyticsService.get_global_stats()
