"""
threat_service.py - Blocked threat management business logic
"""

from datetime import datetime
from typing import Optional, List

from app.db.models.threat import BlockedThreat, ThreatType, ThreatStatus
from app.db.models.scan import ScanRequest, Channel
from app.schemas.threat import (
    ThreatResponse,
    ThreatListResponse,
    ThreatReport,
    ThreatUpdate,
)


class ThreatService:
    """
    Service for blocked threat management.
    """
    
    @staticmethod
    async def get_threats(
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        threat_type: Optional[str] = None
    ) -> ThreatListResponse:
        """
        Get paginated list of blocked threats for user.
        """
        # Build query
        query = BlockedThreat.find(BlockedThreat.user_id == user_id)
        
        if status:
            query = query.find(BlockedThreat.status == status)
        
        if threat_type:
            query = query.find(BlockedThreat.threat_type == threat_type)
        
        # Get total count
        total = await query.count()
        
        # Get paginated results
        skip = (page - 1) * limit
        threats = await query.sort(-BlockedThreat.blocked_at).skip(skip).limit(limit).to_list()
        
        items = [
            ThreatResponse(
                id=str(threat.id),
                threat_type=threat.threat_type.value,
                sender_info=threat.sender_info,
                message_preview=threat.message_preview,
                risk_score=threat.risk_score,
                status=threat.status.value,
                action_taken=threat.action_taken,
                blocked_at=threat.blocked_at,
                user_notes=threat.user_notes,
            )
            for threat in threats
        ]
        
        return ThreatListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(skip + limit) < total,
        )
    
    @staticmethod
    async def get_threat_detail(
        user_id: str,
        threat_id: str
    ) -> Optional[ThreatResponse]:
        """
        Get detailed threat information.
        """
        threat = await BlockedThreat.get(threat_id)
        
        if not threat or threat.user_id != user_id:
            return None
        
        return ThreatResponse(
            id=str(threat.id),
            threat_type=threat.threat_type.value,
            sender_info=threat.sender_info,
            message_preview=threat.message_preview,
            risk_score=threat.risk_score,
            status=threat.status.value,
            action_taken=threat.action_taken,
            blocked_at=threat.blocked_at,
            user_notes=threat.user_notes,
        )
    
    @staticmethod
    async def report_threat(
        user_id: str,
        data: ThreatReport
    ) -> ThreatResponse:
        """
        Manually report a new threat.
        """
        # Determine threat type
        threat_type = ThreatType.OTHER
        if data.threat_type:
            try:
                threat_type = ThreatType(data.threat_type)
            except ValueError:
                pass
        
        # Create threat entry
        threat = BlockedThreat(
            user_id=user_id,
            threat_type=threat_type,
            sender_info=data.sender_info,
            message_preview=data.message_text[:200],
            risk_score=0.0,  # Manual report, no confidence score
            status=ThreatStatus.REPORTED,
            action_taken="reported",
            user_notes=data.notes,
        )
        await threat.insert()
        
        # Also create a scan record
        scan = ScanRequest(
            user_id=user_id,
            message_text=data.message_text,
            channel=Channel(data.channel) if data.channel in Channel.__members__ else Channel.OTHER,
            sender_info=data.sender_info,
            is_scam=True,  # User reported as threat
            confidence=0.0,  # Manual report
            scam_type=data.threat_type,
            analysis={"source": "user_report"},
        )
        await scan.insert()
        
        # Link scan to threat
        threat.scan_id = str(scan.id)
        await threat.save()
        
        return ThreatResponse(
            id=str(threat.id),
            threat_type=threat.threat_type.value,
            sender_info=threat.sender_info,
            message_preview=threat.message_preview,
            risk_score=threat.risk_score,
            status=threat.status.value,
            action_taken=threat.action_taken,
            blocked_at=threat.blocked_at,
            user_notes=threat.user_notes,
        )
    
    @staticmethod
    async def update_threat(
        user_id: str,
        threat_id: str,
        data: ThreatUpdate
    ) -> Optional[ThreatResponse]:
        """
        Update a threat (whitelist, add notes).
        """
        threat = await BlockedThreat.get(threat_id)
        
        if not threat or threat.user_id != user_id:
            return None
        
        if data.status == "whitelisted":
            await threat.whitelist()
        
        if data.user_notes is not None:
            threat.user_notes = data.user_notes
            await threat.save()
        
        return ThreatResponse(
            id=str(threat.id),
            threat_type=threat.threat_type.value,
            sender_info=threat.sender_info,
            message_preview=threat.message_preview,
            risk_score=threat.risk_score,
            status=threat.status.value,
            action_taken=threat.action_taken,
            blocked_at=threat.blocked_at,
            user_notes=threat.user_notes,
        )
    
    @staticmethod
    async def delete_threat(
        user_id: str,
        threat_id: str
    ) -> bool:
        """
        Delete a threat from list.
        """
        threat = await BlockedThreat.get(threat_id)
        
        if not threat or threat.user_id != user_id:
            return False
        
        await threat.delete()
        return True
    
    @staticmethod
    async def get_active_threat_count(user_id: str) -> int:
        """
        Get count of active (blocked) threats.
        """
        return await BlockedThreat.find(
            BlockedThreat.user_id == user_id,
            BlockedThreat.status == ThreatStatus.BLOCKED
        ).count()
