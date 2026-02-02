"""
scan_service.py - Message scanning business logic
"""

from datetime import datetime, timedelta
from typing import Optional, List
import re

from app.db.models.scan import ScanRequest, Channel
from app.db.models.threat import BlockedThreat, ThreatType, ThreatStatus
from app.db.models.user_settings import UserSettings
from app.db.models.subscription import Subscription
from app.schemas.scan import (
    ScanInput,
    ScanResponse,
    ScanHistoryItem,
    ScanHistoryResponse,
    ScanDetail,
)

# Import existing scam detection
from app.scam_detector import detect_scam
from app.intelligence import extract_from_text


class ScanService:
    """
    Service for message scanning operations.
    """
    
    # Scam type mapping
    SCAM_TYPES = {
        "phishing": ThreatType.PHISHING,
        "lottery": ThreatType.LOTTERY,
        "tech_support": ThreatType.TECH_SUPPORT,
        "romance": ThreatType.ROMANCE,
        "investment": ThreatType.INVESTMENT,
        "banking": ThreatType.BANKING,
        "impersonation": ThreatType.IMPERSONATION,
    }
    
    @staticmethod
    async def scan_message(
        user_id: str,
        data: ScanInput
    ) -> ScanResponse:
        """
        Scan a message for scam detection.
        
        Returns:
            ScanResponse with results
        """
        # Check scan limits
        await ScanService._check_scan_limit(user_id)
        
        # Use existing scam detector
        detection_result = detect_scam(data.message_text)
        
        is_scam = detection_result.get("is_scam", False)
        confidence = detection_result.get("confidence", 0.0)
        scam_type = detection_result.get("scam_type")
        indicators = detection_result.get("indicators", [])
        
        # Extract entities using existing intelligence module
        intel = extract_from_text(data.message_text)
        
        # Determine risk level
        risk_level = ScanService._calculate_risk_level(confidence)
        
        # Generate recommendation
        recommendation = ScanService._generate_recommendation(
            is_scam, scam_type, confidence
        )
        
        # Get user settings for auto-block
        settings = await UserSettings.get_or_create(user_id)
        auto_blocked = False
        
        if is_scam and settings.auto_block and confidence >= 0.7:
            auto_blocked = True
        
        # Save to database
        scan = ScanRequest(
            user_id=user_id,
            message_text=data.message_text,
            channel=Channel(data.channel.value),
            sender_info=data.sender_info,
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            analysis={
                "indicators": indicators,
                "risk_level": risk_level,
            },
            extracted_phones=intel.phones if hasattr(intel, 'phones') else [],
            extracted_emails=intel.emails if hasattr(intel, 'emails') else [],
            extracted_urls=intel.urls if hasattr(intel, 'urls') else [],
            extracted_upis=intel.upi_ids if hasattr(intel, 'upi_ids') else [],
            auto_blocked=auto_blocked,
        )
        await scan.insert()
        
        # Update subscription scan count
        await ScanService._increment_scan_count(user_id)
        
        # Create blocked threat if auto-blocked
        if auto_blocked:
            await ScanService._create_blocked_threat(
                user_id=user_id,
                scan_id=str(scan.id),
                scam_type=scam_type,
                sender_info=data.sender_info,
                message_text=data.message_text,
                confidence=confidence,
            )
        
        return ScanResponse(
            scan_id=str(scan.id),
            is_scam=is_scam,
            confidence=confidence,
            scam_type=scam_type,
            risk_level=risk_level,
            indicators=indicators,
            recommendation=recommendation,
            extracted_phones=scan.extracted_phones,
            extracted_emails=scan.extracted_emails,
            extracted_urls=scan.extracted_urls,
            auto_blocked=auto_blocked,
        )
    
    @staticmethod
    async def get_scan_history(
        user_id: str,
        page: int = 1,
        limit: int = 20,
        filter_scams: Optional[bool] = None
    ) -> ScanHistoryResponse:
        """
        Get paginated scan history for user.
        """
        # Build query
        query = ScanRequest.find(ScanRequest.user_id == user_id)
        
        if filter_scams is not None:
            query = query.find(ScanRequest.is_scam == filter_scams)
        
        # Get total count
        total = await query.count()
        
        # Get paginated results
        skip = (page - 1) * limit
        scans = await query.sort(-ScanRequest.created_at).skip(skip).limit(limit).to_list()
        
        items = [
            ScanHistoryItem(
                id=str(scan.id),
                message_preview=scan.get_preview(),
                channel=scan.channel.value,
                is_scam=scan.is_scam,
                confidence=scan.confidence,
                scam_type=scan.scam_type,
                created_at=scan.created_at,
            )
            for scan in scans
        ]
        
        return ScanHistoryResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(skip + limit) < total,
        )
    
    @staticmethod
    async def get_scan_detail(
        user_id: str,
        scan_id: str
    ) -> Optional[ScanDetail]:
        """
        Get detailed scan information.
        """
        scan = await ScanRequest.get(scan_id)
        
        if not scan or scan.user_id != user_id:
            return None
        
        return ScanDetail(
            id=str(scan.id),
            message_text=scan.message_text,
            channel=scan.channel.value,
            sender_info=scan.sender_info,
            is_scam=scan.is_scam,
            confidence=scan.confidence,
            scam_type=scan.scam_type,
            risk_level=scan.analysis.get("risk_level", "unknown"),
            analysis=scan.analysis,
            indicators=scan.analysis.get("indicators", []),
            recommendation=ScanService._generate_recommendation(
                scan.is_scam, scan.scam_type, scan.confidence
            ),
            extracted_phones=scan.extracted_phones,
            extracted_emails=scan.extracted_emails,
            extracted_urls=scan.extracted_urls,
            extracted_upis=scan.extracted_upis,
            user_feedback=scan.user_feedback,
            created_at=scan.created_at,
            auto_blocked=scan.auto_blocked,
        )
    
    @staticmethod
    async def add_feedback(
        user_id: str,
        scan_id: str,
        feedback: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Add user feedback to a scan.
        """
        scan = await ScanRequest.get(scan_id)
        
        if not scan or scan.user_id != user_id:
            return False
        
        scan.user_feedback = feedback
        if comment:
            scan.analysis["feedback_comment"] = comment
        
        await scan.save()
        
        # If false positive, remove from blocked threats
        if feedback == "false_positive":
            threat = await BlockedThreat.find_one(
                BlockedThreat.scan_id == scan_id
            )
            if threat:
                await threat.whitelist()
        
        return True
    
    @staticmethod
    def _calculate_risk_level(confidence: float) -> str:
        """Calculate risk level from confidence score."""
        if confidence >= 0.9:
            return "critical"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _generate_recommendation(
        is_scam: bool,
        scam_type: Optional[str],
        confidence: float
    ) -> str:
        """Generate recommendation based on scan results."""
        if not is_scam:
            if confidence < 0.3:
                return "This message appears to be safe. However, always be cautious with unsolicited messages."
            else:
                return "This message has some suspicious elements but doesn't appear to be a scam. Exercise caution."
        
        recommendations = {
            "phishing": "This appears to be a phishing attempt. Do not click any links or provide personal information. Report to your bank if it claims to be from them.",
            "lottery": "This is a lottery/prize scam. Legitimate lotteries never ask for upfront fees. Delete this message.",
            "tech_support": "This is a tech support scam. Microsoft, Google, and other companies never call or message about computer problems. Hang up or ignore.",
            "romance": "This may be a romance scam. Be very careful about sending money to someone you've never met in person.",
            "investment": "This appears to be an investment scam. Be wary of guaranteed high returns. Consult a licensed financial advisor.",
            "banking": "This is likely a banking scam. Your bank will never ask for passwords or PINs via SMS. Contact your bank directly using official channels.",
            "impersonation": "Someone may be impersonating a known person or organization. Verify through official channels before responding.",
        }
        
        base_recommendation = recommendations.get(
            scam_type,
            "This message shows signs of being a scam. Do not respond, click links, or share personal information."
        )
        
        if confidence >= 0.9:
            return f"⚠️ HIGH RISK: {base_recommendation}"
        elif confidence >= 0.7:
            return f"⚠️ {base_recommendation}"
        else:
            return f"Potential scam detected. {base_recommendation}"
    
    @staticmethod
    async def _check_scan_limit(user_id: str):
        """Check if user has exceeded scan limits."""
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if not subscription:
            return  # No subscription = free tier
        
        # For free tier, check daily limit
        if subscription.plan_tier.value == "free":
            if subscription.scans_today >= 10:  # Free tier: 10 scans/day
                raise ValueError("Daily scan limit reached. Upgrade to Pro for unlimited scans.")
    
    @staticmethod
    async def _increment_scan_count(user_id: str):
        """Increment user's scan count."""
        subscription = await Subscription.find_one(
            Subscription.user_id == user_id
        )
        
        if subscription:
            await subscription.increment_scan_count()
    
    @staticmethod
    async def _create_blocked_threat(
        user_id: str,
        scan_id: str,
        scam_type: Optional[str],
        sender_info: Optional[str],
        message_text: str,
        confidence: float
    ):
        """Create a blocked threat entry."""
        threat_type = ScanService.SCAM_TYPES.get(
            scam_type, ThreatType.OTHER
        )
        
        threat = BlockedThreat(
            user_id=user_id,
            scan_id=scan_id,
            threat_type=threat_type,
            sender_info=sender_info,
            message_preview=message_text[:200],
            risk_score=confidence,
            status=ThreatStatus.BLOCKED,
            action_taken="blocked",
        )
        await threat.insert()
