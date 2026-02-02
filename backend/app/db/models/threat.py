"""
threat.py - Blocked threat document
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum


class ThreatStatus(str, Enum):
    BLOCKED = "blocked"
    WHITELISTED = "whitelisted"
    REPORTED = "reported"


class ThreatType(str, Enum):
    PHISHING = "phishing"
    LOTTERY = "lottery"
    TECH_SUPPORT = "tech_support"
    ROMANCE = "romance"
    INVESTMENT = "investment"
    BANKING = "banking"
    IMPERSONATION = "impersonation"
    OTHER = "other"


class BlockedThreat(Document):
    """
    Record of a blocked threat/scam attempt.
    """
    user_id: Annotated[str, Indexed()]  # References User._id
    scan_id: Optional[str] = None  # References ScanRequest._id if from scan
    
    # Threat info
    threat_type: ThreatType = ThreatType.OTHER
    sender_info: Optional[str] = None  # Phone number, email, etc.
    message_preview: str = ""  # First 200 chars
    
    # Status
    status: ThreatStatus = ThreatStatus.BLOCKED
    
    # Risk assessment
    risk_score: float = 0.0  # 0.0 to 1.0
    
    # Action taken
    action_taken: str = "blocked"  # blocked, warned, reported
    
    # Timestamps
    blocked_at: datetime = Field(default_factory=datetime.utcnow)
    whitelisted_at: Optional[datetime] = None
    
    # User notes
    user_notes: Optional[str] = None
    
    class Settings:
        name = "blocked_threats"
        indexes = [
            [("user_id", 1), ("blocked_at", -1)],
            [("threat_type", 1)],
        ]
        
    async def whitelist(self):
        """Mark threat as whitelisted (false positive)"""
        self.status = ThreatStatus.WHITELISTED
        self.whitelisted_at = datetime.utcnow()
        await self.save()
