"""
session.py - Honeypot session document (migrated from in-memory)
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    REPORTED = "reported"


class SessionMessage(Document):
    """
    Embedded document for conversation messages.
    Note: This is not a separate collection, but used as embedded docs.
    """
    sender: str  # "scammer" or "agent"
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedIntel(Document):
    """
    Embedded document for extracted intelligence.
    """
    phones: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    upi_ids: List[str] = Field(default_factory=list)
    names: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    crypto_wallets: List[str] = Field(default_factory=list)
    
    def has_intel(self) -> bool:
        """Check if any intel has been extracted"""
        return any([
            self.phones, self.emails, self.bank_accounts,
            self.upi_ids, self.names, self.urls, self.crypto_wallets
        ])
    
    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "phones": self.phones,
            "emails": self.emails,
            "bank_accounts": self.bank_accounts,
            "upi_ids": self.upi_ids,
            "names": self.names,
            "urls": self.urls,
            "crypto_wallets": self.crypto_wallets,
        }


class HoneypotSession(Document):
    """
    Honeypot engagement session with scammer.
    Replaces the in-memory session_manager.
    """
    session_id: Annotated[str, Indexed(unique=True)]  # External session identifier
    
    # Classification
    scam_type: Optional[str] = None
    scam_confidence: float = 0.0
    
    # Status
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Conversation
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    # Each message: {"sender": str, "text": str, "timestamp": str, "metadata": {}}
    
    # Extracted intelligence
    intel: Dict[str, List[str]] = Field(default_factory=lambda: {
        "phones": [],
        "emails": [],
        "bank_accounts": [],
        "upi_ids": [],
        "names": [],
        "urls": [],
        "crypto_wallets": [],
    })
    
    # Linked scammer fingerprint
    scammer_fingerprint_id: Optional[str] = None
    
    # Engagement metrics
    total_messages: int = 0
    scammer_messages: int = 0
    agent_messages: int = 0
    engagement_duration_seconds: int = 0
    
    # Emotional state tracking (from v3.5)
    emotional_state: str = "neutral"
    
    # Callback tracking
    callback_sent: bool = False
    callback_response: Optional[Dict[str, Any]] = None
    
    # Metadata
    channel: str = "SMS"
    language: str = "en"
    locale: str = "IN"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    
    class Settings:
        name = "honeypot_sessions"
        indexes = [
            [("status", 1), ("created_at", -1)],
            [("scam_type", 1)],
        ]
    
    @property
    def message_count(self) -> int:
        return len(self.messages)
    
    def add_message(self, sender: str, text: str, timestamp: str = None, metadata: dict = None):
        """Add a message to conversation history"""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        self.messages.append({
            "sender": sender,
            "text": text,
            "timestamp": timestamp,
            "metadata": metadata or {}
        })
        
        self.total_messages += 1
        if sender == "scammer":
            self.scammer_messages += 1
        else:
            self.agent_messages += 1
            
        self.updated_at = datetime.utcnow()
    
    def get_history_for_prompt(self, max_messages: int = 20) -> str:
        """Format conversation for LLM prompt"""
        recent = self.messages[-max_messages:]
        
        formatted = []
        for msg in recent:
            role = "Scammer" if msg["sender"] == "scammer" else "You"
            formatted.append(f"{role}: {msg['text']}")
        
        return "\n".join(formatted)
    
    def add_intel(self, intel_type: str, value: str):
        """Add extracted intelligence"""
        if intel_type in self.intel:
            if value not in self.intel[intel_type]:
                self.intel[intel_type].append(value)
    
    async def close_session(self):
        """Close the session"""
        self.status = SessionStatus.CLOSED
        self.closed_at = datetime.utcnow()
        
        # Calculate engagement duration
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            self.engagement_duration_seconds = int(delta.total_seconds())
        
        await self.save()
