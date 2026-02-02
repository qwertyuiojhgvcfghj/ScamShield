"""
threats.py - Blocked threats routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional

from app.schemas.threat import (
    ThreatResponse,
    ThreatListResponse,
    ThreatReport,
    ThreatUpdate,
)
from app.services.threat_service import ThreatService
from app.core.dependencies import get_current_active_user
from app.db.models.user import User


router = APIRouter(prefix="/threats", tags=["Threats"])


@router.get(
    "/",
    response_model=ThreatListResponse,
    summary="Get blocked threats"
)
async def get_threats(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    threat_type: Optional[str] = Query(None, description="Filter by threat type"),
    user: User = Depends(get_current_active_user)
):
    """
    Get list of blocked threats with pagination.
    
    - **page**: Page number (starts at 1)
    - **limit**: Number of items per page (max 100)
    - **status**: Filter by status (blocked, whitelisted, reported)
    - **threat_type**: Filter by type (phishing, lottery, etc.)
    """
    return await ThreatService.get_threats(
        user_id=str(user.id),
        page=page,
        limit=limit,
        status=status_filter,
        threat_type=threat_type
    )


@router.get(
    "/{threat_id}",
    response_model=ThreatResponse,
    summary="Get threat details"
)
async def get_threat_detail(
    threat_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific threat.
    """
    result = await ThreatService.get_threat_detail(str(user.id), threat_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    return result


@router.post(
    "/report",
    response_model=ThreatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a threat manually"
)
async def report_threat(
    data: ThreatReport,
    user: User = Depends(get_current_active_user)
):
    """
    Manually report a scam/threat message.
    
    - **message_text**: The scam message content
    - **sender_info**: Phone number or email of sender
    - **channel**: SMS, Email, WhatsApp, etc.
    - **threat_type**: Type of scam (optional)
    - **notes**: Additional notes (optional)
    """
    return await ThreatService.report_threat(str(user.id), data)


@router.put(
    "/{threat_id}",
    response_model=ThreatResponse,
    summary="Update threat"
)
async def update_threat(
    threat_id: str,
    data: ThreatUpdate,
    user: User = Depends(get_current_active_user)
):
    """
    Update a threat (whitelist or add notes).
    
    - **status**: Set to "whitelisted" to mark as false positive
    - **user_notes**: Add personal notes
    """
    result = await ThreatService.update_threat(str(user.id), threat_id, data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    return result


@router.post(
    "/{threat_id}/whitelist",
    summary="Whitelist a threat"
)
async def whitelist_threat(
    threat_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Mark a threat as a false positive (whitelist it).
    """
    data = ThreatUpdate(status="whitelisted")
    result = await ThreatService.update_threat(str(user.id), threat_id, data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    return {
        "status": "success",
        "message": "Threat whitelisted successfully"
    }


@router.delete(
    "/{threat_id}",
    summary="Delete threat from list"
)
async def delete_threat(
    threat_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Remove a threat from your blocked list.
    """
    success = await ThreatService.delete_threat(str(user.id), threat_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    return {
        "status": "success",
        "message": "Threat removed from list"
    }
