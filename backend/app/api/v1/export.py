"""
export.py - Export endpoints for scan history and data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
import csv
import json
import io

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.models.scan import ScanRequest
from app.db.models.threat import BlockedThreat


router = APIRouter(prefix="/export", tags=["Export"])


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


@router.get("/scans")
async def export_scan_history(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    current_user: User = Depends(get_current_user)
):
    """
    Export scan history for the current user.
    
    Supports CSV and JSON formats.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Fetch scans
    scans = await ScanRequest.find(
        ScanRequest.user_id == str(current_user.id),
        ScanRequest.created_at >= start_date
    ).sort(-ScanRequest.created_at).to_list()
    
    if not scans:
        raise HTTPException(status_code=404, detail="No scans found in the specified period")
    
    if format == ExportFormat.CSV:
        return _export_scans_csv(scans, current_user.email)
    else:
        return _export_scans_json(scans)


def _export_scans_csv(scans: List[ScanRequest], user_email: str) -> StreamingResponse:
    """Generate CSV export of scans."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Scan ID",
        "Date",
        "Time",
        "Content Preview",
        "Risk Score",
        "Is Scam",
        "Scam Type",
        "Confidence",
        "Status"
    ])
    
    # Data rows
    for scan in scans:
        writer.writerow([
            str(scan.id),
            scan.created_at.strftime("%Y-%m-%d"),
            scan.created_at.strftime("%H:%M:%S"),
            (scan.content[:100] + "...") if len(scan.content) > 100 else scan.content,
            scan.result.get("risk_score", 0) if scan.result else 0,
            scan.result.get("is_scam", False) if scan.result else False,
            scan.result.get("scam_type", "unknown") if scan.result else "unknown",
            scan.result.get("confidence", 0) if scan.result else 0,
            scan.status
        ])
    
    output.seek(0)
    
    filename = f"scamshield_scans_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(len(scans)),
            "X-Export-User": user_email
        }
    )


def _export_scans_json(scans: List[ScanRequest]) -> StreamingResponse:
    """Generate JSON export of scans."""
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "total_scans": len(scans),
        "scans": []
    }
    
    for scan in scans:
        export_data["scans"].append({
            "id": str(scan.id),
            "created_at": scan.created_at.isoformat(),
            "content": scan.content,
            "content_type": scan.content_type,
            "result": scan.result,
            "status": scan.status
        })
    
    output = json.dumps(export_data, indent=2, default=str)
    filename = f"scamshield_scans_{datetime.utcnow().strftime('%Y%m%d')}.json"
    
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(len(scans))
        }
    )


@router.get("/threats")
async def export_blocked_threats(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    current_user: User = Depends(get_current_user)
):
    """
    Export blocked threats for the current user.
    
    Supports CSV and JSON formats.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Fetch threats
    threats = await BlockedThreat.find(
        BlockedThreat.user_id == str(current_user.id),
        BlockedThreat.created_at >= start_date
    ).sort(-BlockedThreat.created_at).to_list()
    
    if not threats:
        raise HTTPException(status_code=404, detail="No threats found in the specified period")
    
    if format == ExportFormat.CSV:
        return _export_threats_csv(threats)
    else:
        return _export_threats_json(threats)


def _export_threats_csv(threats: List[BlockedThreat]) -> StreamingResponse:
    """Generate CSV export of threats."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Threat ID",
        "Date",
        "Type",
        "Sender",
        "Message Preview",
        "Risk Score",
        "Status",
        "Action Taken"
    ])
    
    # Data rows
    for threat in threats:
        writer.writerow([
            str(threat.id),
            threat.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            threat.threat_type.value,
            threat.sender_info or "Unknown",
            (threat.message_preview[:100] + "...") if len(threat.message_preview) > 100 else threat.message_preview,
            threat.risk_score,
            threat.status.value,
            threat.action_taken
        ])
    
    output.seek(0)
    
    filename = f"scamshield_threats_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(len(threats))
        }
    )


def _export_threats_json(threats: List[BlockedThreat]) -> StreamingResponse:
    """Generate JSON export of threats."""
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "total_threats": len(threats),
        "threats": []
    }
    
    for threat in threats:
        export_data["threats"].append({
            "id": str(threat.id),
            "created_at": threat.created_at.isoformat(),
            "threat_type": threat.threat_type.value,
            "sender_info": threat.sender_info,
            "message_preview": threat.message_preview,
            "risk_score": threat.risk_score,
            "status": threat.status.value,
            "action_taken": threat.action_taken
        })
    
    output = json.dumps(export_data, indent=2, default=str)
    filename = f"scamshield_threats_{datetime.utcnow().strftime('%Y%m%d')}.json"
    
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(len(threats))
        }
    )


@router.get("/report")
async def export_security_report(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive security report.
    
    Includes:
    - Summary statistics
    - Threat breakdown by type
    - Risk score distribution
    - Timeline of incidents
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Fetch data
    scans = await ScanRequest.find(
        ScanRequest.user_id == str(current_user.id),
        ScanRequest.created_at >= start_date
    ).to_list()
    
    threats = await BlockedThreat.find(
        BlockedThreat.user_id == str(current_user.id),
        BlockedThreat.created_at >= start_date
    ).to_list()
    
    # Calculate statistics
    total_scans = len(scans)
    scam_detected = sum(1 for s in scans if s.result and s.result.get("is_scam", False))
    safe_messages = total_scans - scam_detected
    
    # Threat type breakdown
    threat_types = {}
    for threat in threats:
        tt = threat.threat_type.value
        threat_types[tt] = threat_types.get(tt, 0) + 1
    
    # Risk score distribution
    risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for scan in scans:
        if scan.result:
            score = scan.result.get("risk_score", 0)
            if score < 0.3:
                risk_distribution["low"] += 1
            elif score < 0.6:
                risk_distribution["medium"] += 1
            elif score < 0.85:
                risk_distribution["high"] += 1
            else:
                risk_distribution["critical"] += 1
    
    report = {
        "report_generated": datetime.utcnow().isoformat(),
        "report_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "user": {
            "email": current_user.email,
            "name": current_user.full_name
        },
        "summary": {
            "total_scans": total_scans,
            "scams_detected": scam_detected,
            "safe_messages": safe_messages,
            "detection_rate": round(scam_detected / total_scans * 100, 2) if total_scans > 0 else 0,
            "total_threats_blocked": len(threats)
        },
        "threat_breakdown": threat_types,
        "risk_distribution": risk_distribution,
        "protection_score": calculate_protection_score(total_scans, scam_detected, len(threats))
    }
    
    return report


def calculate_protection_score(total_scans: int, scams_detected: int, threats_blocked: int) -> dict:
    """Calculate an overall protection score."""
    if total_scans == 0:
        return {"score": 100, "grade": "A", "status": "No threats detected"}
    
    # Base score starts at 100
    score = 100
    
    # Deduct points for scams that got through (assuming some weren't blocked)
    # This is a simplified calculation
    if scams_detected > 0:
        blocked_ratio = min(threats_blocked / scams_detected, 1.0)
        score = int(blocked_ratio * 100)
    
    # Determine grade
    if score >= 90:
        grade, status = "A", "Excellent protection"
    elif score >= 80:
        grade, status = "B", "Good protection"
    elif score >= 70:
        grade, status = "C", "Moderate protection"
    elif score >= 60:
        grade, status = "D", "Needs improvement"
    else:
        grade, status = "F", "Critical - review security settings"
    
    return {"score": score, "grade": grade, "status": status}
