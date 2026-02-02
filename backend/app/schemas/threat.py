"""
threat.py - Blocked threat schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ThreatResponse(BaseModel):
    """Schema for threat response"""
    id: str
    threat_type: str
    sender_info: Optional[str] = None
    message_preview: str
    risk_score: float
    status: str  # blocked, whitelisted, reported
    action_taken: str
    blocked_at: datetime
    user_notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "threat_type": "phishing",
                "sender_info": "+911234567890",
                "message_preview": "Your bank account has been...",
                "risk_score": 0.92,
                "status": "blocked",
                "action_taken": "blocked",
                "blocked_at": "2026-02-01T10:30:00Z"
            }
        }


class ThreatListResponse(BaseModel):
    """Schema for paginated threat list"""
    items: List[ThreatResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ThreatReport(BaseModel):
    """Schema for manually reporting a threat"""
    message_text: str = Field(..., min_length=1, max_length=5000)
    sender_info: Optional[str] = None
    channel: str = "SMS"
    threat_type: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_text": "Dear customer, your KYC is expired. Update now: suspicious-link.com",
                "sender_info": "+911234567890",
                "channel": "SMS",
                "threat_type": "phishing",
                "notes": "Received this message 3 times today"
            }
        }


class ThreatUpdate(BaseModel):
    """Schema for updating a threat"""
    status: Optional[str] = Field(None, pattern="^(blocked|whitelisted)$")
    user_notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "whitelisted",
                "user_notes": "This was actually from my bank"
            }
        }
