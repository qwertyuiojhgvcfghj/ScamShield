"""
scammer.py - Scammer fingerprint document
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime


class ScammerFingerprint(Document):
    """
    Known scammer fingerprint for tracking repeat offenders.
    """
    fingerprint_hash: Annotated[str, Indexed(unique=True)]  # Hash of identifiers
    
    # Collected identifiers
    phone_numbers: List[str] = Field(default_factory=list)
    email_addresses: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    upi_ids: List[str] = Field(default_factory=list)
    crypto_wallets: List[str] = Field(default_factory=list)
    
    # Scam patterns
    scam_types: List[str] = Field(default_factory=list)
    tactics: List[str] = Field(default_factory=list)
    
    # Session history
    session_ids: List[str] = Field(default_factory=list)
    total_sessions: int = 0
    
    # Risk assessment
    risk_score: float = 0.0  # 0.0 to 1.0
    threat_level: str = "low"  # low, medium, high, critical
    
    # Activity timeline
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Notes/flags
    is_reported: bool = False
    reported_to: List[str] = Field(default_factory=list)  # Authorities notified
    notes: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "scammer_fingerprints"
        indexes = [
            [("risk_score", -1)],
            [("last_seen", -1)],
        ]
    
    def add_session(self, session_id: str):
        """Add a session to this scammer's history"""
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)
            self.total_sessions += 1
            self.last_seen = datetime.utcnow()
            
            # Increase risk score with more sessions
            self.risk_score = min(1.0, self.risk_score + 0.1)
            self._update_threat_level()
    
    def add_identifier(self, id_type: str, value: str):
        """Add an identifier to the fingerprint"""
        id_map = {
            "phone": self.phone_numbers,
            "email": self.email_addresses,
            "bank": self.bank_accounts,
            "upi": self.upi_ids,
            "crypto": self.crypto_wallets,
        }
        
        if id_type in id_map and value not in id_map[id_type]:
            id_map[id_type].append(value)
    
    def _update_threat_level(self):
        """Update threat level based on risk score"""
        if self.risk_score >= 0.8:
            self.threat_level = "critical"
        elif self.risk_score >= 0.6:
            self.threat_level = "high"
        elif self.risk_score >= 0.3:
            self.threat_level = "medium"
        else:
            self.threat_level = "low"
    
    @classmethod
    async def find_by_identifier(cls, value: str) -> Optional["ScammerFingerprint"]:
        """Find scammer by any identifier"""
        return await cls.find_one({
            "$or": [
                {"phone_numbers": value},
                {"email_addresses": value},
                {"bank_accounts": value},
                {"upi_ids": value},
                {"crypto_wallets": value},
            ]
        })
