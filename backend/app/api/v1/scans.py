"""
scans.py - Message scanning routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional

from app.schemas.scan import (
    ScanInput,
    ScanResponse,
    ScanHistoryResponse,
    ScanDetail,
    ScanFeedback,
)
from app.services.scan_service import ScanService
from app.core.dependencies import get_current_active_user
from app.db.models.user import User


router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post(
    "/",
    response_model=ScanResponse,
    summary="Scan a message for scams"
)
async def scan_message(
    data: ScanInput,
    user: User = Depends(get_current_active_user)
):
    """
    Scan a message to check if it's a scam.
    
    - **message_text**: The message content to analyze
    - **channel**: Where the message came from (SMS, Email, WhatsApp, etc.)
    - **sender_info**: Optional sender phone number or email
    
    Returns detailed analysis including:
    - Whether it's a scam
    - Confidence score (0-1)
    - Scam type classification
    - Risk level
    - Recommended action
    """
    try:
        result = await ScanService.scan_message(str(user.id), data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )


@router.get(
    "/history",
    response_model=ScanHistoryResponse,
    summary="Get scan history"
)
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    scams_only: Optional[bool] = Query(None, description="Filter for scams only"),
    user: User = Depends(get_current_active_user)
):
    """
    Get the user's scan history with pagination.
    
    - **page**: Page number (starts at 1)
    - **limit**: Number of items per page (max 100)
    - **scams_only**: Set to true to only show detected scams
    """
    return await ScanService.get_scan_history(
        user_id=str(user.id),
        page=page,
        limit=limit,
        filter_scams=scams_only
    )


@router.get(
    "/{scan_id}",
    response_model=ScanDetail,
    summary="Get scan details"
)
async def get_scan_detail(
    scan_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific scan.
    """
    result = await ScanService.get_scan_detail(str(user.id), scan_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return result


@router.post(
    "/{scan_id}/feedback",
    summary="Provide feedback on scan"
)
async def add_feedback(
    scan_id: str,
    data: ScanFeedback,
    user: User = Depends(get_current_active_user)
):
    """
    Provide feedback on a scan result.
    
    - **feedback**: One of "correct", "false_positive", "false_negative"
    - **comment**: Optional comment explaining the feedback
    
    This helps improve our detection accuracy.
    """
    success = await ScanService.add_feedback(
        user_id=str(user.id),
        scan_id=scan_id,
        feedback=data.feedback,
        comment=data.comment
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return {
        "status": "success",
        "message": "Feedback recorded. Thank you for helping improve our detection!"
    }
