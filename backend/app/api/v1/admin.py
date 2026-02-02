"""
admin.py - Admin-only routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List

from app.services.analytics_service import AnalyticsService
from app.services.session_service import SessionService
from app.core.dependencies import get_current_admin
from app.db.models.user import User, UserRole
from app.db.models.session import HoneypotSession, SessionStatus
from app.db.models.scammer import ScammerFingerprint
from app.schemas.analytics import HoneypotStats


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    summary="List all users"
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email"),
    admin: User = Depends(get_current_admin)
):
    """
    List all users with pagination (admin only).
    """
    query = User.find()
    
    if search:
        query = query.find({"email": {"$regex": search, "$options": "i"}})
    
    total = await query.count()
    skip = (page - 1) * limit
    users = await query.skip(skip).limit(limit).to_list()
    
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


@router.get(
    "/users/{user_id}",
    summary="Get user details"
)
async def get_user(
    user_id: str,
    admin: User = Depends(get_current_admin)
):
    """
    Get detailed user information (admin only).
    """
    user = await User.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.put(
    "/users/{user_id}/role",
    summary="Change user role"
)
async def change_role(
    user_id: str,
    role: str = Query(..., pattern="^(user|admin)$"),
    admin: User = Depends(get_current_admin)
):
    """
    Change a user's role (admin only).
    """
    user = await User.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = UserRole(role)
    await user.save()
    
    return {
        "status": "success",
        "message": f"User role changed to {role}"
    }


@router.put(
    "/users/{user_id}/ban",
    summary="Ban/unban user"
)
async def toggle_ban(
    user_id: str,
    ban: bool = Query(..., description="True to ban, False to unban"),
    admin: User = Depends(get_current_admin)
):
    """
    Ban or unban a user (admin only).
    """
    user = await User.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = not ban
    await user.save()
    
    action = "banned" if ban else "unbanned"
    return {
        "status": "success",
        "message": f"User {action} successfully"
    }


@router.get(
    "/metrics",
    summary="Get system metrics"
)
async def get_metrics(admin: User = Depends(get_current_admin)):
    """
    Get system-wide metrics (admin only).
    """
    from app.db.models.scan import ScanRequest
    from app.db.models.threat import BlockedThreat
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    today = datetime(now.year, now.month, now.day)
    week_ago = now - timedelta(days=7)
    
    total_users = await User.find().count()
    active_users = await User.find(User.is_active == True).count()
    
    total_scans = await ScanRequest.find().count()
    scans_today = await ScanRequest.find(ScanRequest.created_at >= today).count()
    scans_week = await ScanRequest.find(ScanRequest.created_at >= week_ago).count()
    
    total_threats = await BlockedThreat.find().count()
    
    honeypot_stats = await AnalyticsService.get_honeypot_stats()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "scans": {
            "total": total_scans,
            "today": scans_today,
            "this_week": scans_week,
        },
        "threats": {
            "total_blocked": total_threats,
        },
        "honeypot": honeypot_stats.model_dump(),
    }


@router.get(
    "/sessions",
    summary="List honeypot sessions"
)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_current_admin)
):
    """
    List all honeypot sessions (admin only).
    """
    status_enum = None
    if status_filter:
        try:
            status_enum = SessionStatus(status_filter)
        except ValueError:
            pass
    
    skip = (page - 1) * limit
    sessions = await SessionService.list_sessions(
        status=status_enum,
        limit=limit,
        skip=skip
    )
    
    total = await HoneypotSession.find().count()
    
    return {
        "items": [
            {
                "id": str(s.id),
                "session_id": s.session_id,
                "scam_type": s.scam_type,
                "confidence": s.scam_confidence,
                "status": s.status.value,
                "message_count": s.total_messages,
                "has_intel": bool(s.intel.get("phones") or s.intel.get("emails")),
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get(
    "/sessions/{session_id}",
    summary="Get session details"
)
async def get_session(
    session_id: str,
    admin: User = Depends(get_current_admin)
):
    """
    Get detailed honeypot session information (admin only).
    """
    session = await SessionService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "id": str(session.id),
        "session_id": session.session_id,
        "scam_type": session.scam_type,
        "confidence": session.scam_confidence,
        "status": session.status.value,
        "channel": session.channel,
        "language": session.language,
        "messages": session.messages,
        "intel": session.intel,
        "emotional_state": session.emotional_state,
        "callback_sent": session.callback_sent,
        "total_messages": session.total_messages,
        "engagement_duration": session.engagement_duration_seconds,
        "created_at": session.created_at.isoformat(),
        "closed_at": session.closed_at.isoformat() if session.closed_at else None,
    }


@router.get(
    "/scammers",
    summary="List known scammers"
)
async def list_scammers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    min_risk: float = Query(0, ge=0, le=1, description="Minimum risk score"),
    admin: User = Depends(get_current_admin)
):
    """
    List known scammer fingerprints (admin only).
    """
    query = ScammerFingerprint.find(ScammerFingerprint.risk_score >= min_risk)
    
    total = await query.count()
    skip = (page - 1) * limit
    scammers = await query.sort(-ScammerFingerprint.risk_score).skip(skip).limit(limit).to_list()
    
    return {
        "items": [
            {
                "id": str(s.id),
                "fingerprint_hash": s.fingerprint_hash[:16] + "...",
                "phone_count": len(s.phone_numbers),
                "email_count": len(s.email_addresses),
                "total_sessions": s.total_sessions,
                "risk_score": s.risk_score,
                "threat_level": s.threat_level,
                "scam_types": s.scam_types,
                "first_seen": s.first_seen.isoformat(),
                "last_seen": s.last_seen.isoformat(),
            }
            for s in scammers
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get(
    "/scammers/{scammer_id}",
    summary="Get scammer details"
)
async def get_scammer(
    scammer_id: str,
    admin: User = Depends(get_current_admin)
):
    """
    Get detailed scammer fingerprint (admin only).
    """
    scammer = await ScammerFingerprint.get(scammer_id)
    
    if not scammer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scammer not found"
        )
    
    return {
        "id": str(scammer.id),
        "fingerprint_hash": scammer.fingerprint_hash,
        "phone_numbers": scammer.phone_numbers,
        "email_addresses": scammer.email_addresses,
        "bank_accounts": scammer.bank_accounts,
        "upi_ids": scammer.upi_ids,
        "scam_types": scammer.scam_types,
        "tactics": scammer.tactics,
        "total_sessions": scammer.total_sessions,
        "session_ids": scammer.session_ids,
        "risk_score": scammer.risk_score,
        "threat_level": scammer.threat_level,
        "is_reported": scammer.is_reported,
        "reported_to": scammer.reported_to,
        "notes": scammer.notes,
        "first_seen": scammer.first_seen.isoformat(),
        "last_seen": scammer.last_seen.isoformat(),
    }
