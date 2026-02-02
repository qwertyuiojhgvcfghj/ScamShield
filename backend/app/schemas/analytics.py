"""
analytics.py - Analytics and dashboard schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    # Overview
    total_scans: int
    scams_detected: int
    scams_blocked: int
    protection_rate: float  # percentage
    
    # Today's stats
    scans_today: int
    scams_today: int
    
    # This month
    scans_this_month: int
    scams_this_month: int
    
    # Active threats
    active_threats: int
    
    # Trend (vs last period)
    scam_trend: float  # percentage change
    
    # Account info
    current_plan: str
    scans_remaining_today: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scans": 1547,
                "scams_detected": 234,
                "scams_blocked": 228,
                "protection_rate": 97.4,
                "scans_today": 23,
                "scams_today": 3,
                "scans_this_month": 456,
                "scams_this_month": 67,
                "active_threats": 7,
                "scam_trend": -12.5,
                "current_plan": "pro",
                "scans_remaining_today": 977
            }
        }


class TrendDataPoint(BaseModel):
    """Schema for a single trend data point"""
    date: date
    scans: int
    scams_detected: int
    scams_blocked: int


class TrendData(BaseModel):
    """Schema for trend data over time"""
    period: str  # "7d", "30d", "90d"
    data_points: List[TrendDataPoint]
    
    # Summary
    total_scans: int
    total_scams: int
    avg_daily_scans: float
    avg_daily_scams: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "30d",
                "data_points": [
                    {"date": "2026-01-02", "scans": 45, "scams_detected": 7, "scams_blocked": 7},
                    {"date": "2026-01-03", "scans": 52, "scams_detected": 9, "scams_blocked": 8}
                ],
                "total_scans": 1456,
                "total_scams": 234,
                "avg_daily_scans": 48.5,
                "avg_daily_scams": 7.8
            }
        }


class ScamTypeBreakdown(BaseModel):
    """Schema for scam type breakdown"""
    scam_type: str
    count: int
    percentage: float
    trend: float  # vs last period
    
    class Config:
        json_schema_extra = {
            "example": {
                "scam_type": "phishing",
                "count": 87,
                "percentage": 37.2,
                "trend": 5.3
            }
        }


class ScamTypeAnalytics(BaseModel):
    """Schema for scam type analytics"""
    breakdown: List[ScamTypeBreakdown]
    total_scams: int
    most_common: str
    fastest_growing: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "breakdown": [
                    {"scam_type": "phishing", "count": 87, "percentage": 37.2, "trend": 5.3},
                    {"scam_type": "lottery", "count": 56, "percentage": 23.9, "trend": -2.1},
                    {"scam_type": "tech_support", "count": 43, "percentage": 18.4, "trend": 12.8}
                ],
                "total_scams": 234,
                "most_common": "phishing",
                "fastest_growing": "tech_support"
            }
        }


class GlobalStats(BaseModel):
    """Schema for global/public statistics (homepage)"""
    total_scams_blocked: int
    total_users_protected: int
    detection_accuracy: float
    avg_response_time_ms: int
    scams_blocked_today: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scams_blocked": 847293,
                "total_users_protected": 2100000,
                "detection_accuracy": 99.2,
                "avg_response_time_ms": 150,
                "scams_blocked_today": 1247
            }
        }


class HoneypotStats(BaseModel):
    """Schema for honeypot engagement statistics"""
    total_sessions: int
    active_sessions: int
    total_intel_extracted: int
    scammers_identified: int
    avg_engagement_duration_seconds: int
    top_scam_types: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 1234,
                "active_sessions": 5,
                "total_intel_extracted": 567,
                "scammers_identified": 89,
                "avg_engagement_duration_seconds": 1800,
                "top_scam_types": [
                    {"type": "tech_support", "count": 45},
                    {"type": "banking", "count": 38}
                ]
            }
        }
