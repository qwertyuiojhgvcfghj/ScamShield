"""
scan.py - Message scan schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ChannelType(str, Enum):
    SMS = "SMS"
    EMAIL = "Email"
    WHATSAPP = "WhatsApp"
    TELEGRAM = "Telegram"
    OTHER = "Other"


class ScanInput(BaseModel):
    """Schema for scan request input"""
    message_text: str = Field(..., min_length=1, max_length=5000)
    channel: ChannelType = ChannelType.SMS
    sender_info: Optional[str] = None  # Phone number or email
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_text": "Congratulations! You've won Rs 10,00,000. Click here to claim: bit.ly/claim-prize",
                "channel": "SMS",
                "sender_info": "+911234567890"
            }
        }


class ScanResponse(BaseModel):
    """Schema for scan result response"""
    scan_id: str
    is_scam: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    scam_type: Optional[str] = None
    risk_level: str  # low, medium, high, critical
    
    # Analysis details
    indicators: List[str] = []
    recommendation: str
    
    # Extracted entities
    extracted_phones: List[str] = []
    extracted_emails: List[str] = []
    extracted_urls: List[str] = []
    
    # Was it auto-blocked?
    auto_blocked: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "507f1f77bcf86cd799439011",
                "is_scam": True,
                "confidence": 0.95,
                "scam_type": "lottery",
                "risk_level": "high",
                "indicators": [
                    "Prize/lottery claim",
                    "Urgency language",
                    "Suspicious URL (bit.ly)"
                ],
                "recommendation": "This is likely a lottery scam. Do not click any links or share personal information.",
                "extracted_urls": ["bit.ly/claim-prize"],
                "auto_blocked": True
            }
        }


class ScanHistoryItem(BaseModel):
    """Schema for scan history list item"""
    id: str
    message_preview: str  # First 100 chars
    channel: str
    is_scam: bool
    confidence: float
    scam_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "message_preview": "Congratulations! You've won Rs 10,00,000...",
                "channel": "SMS",
                "is_scam": True,
                "confidence": 0.95,
                "scam_type": "lottery",
                "created_at": "2026-02-01T10:30:00Z"
            }
        }


class ScanHistoryResponse(BaseModel):
    """Schema for paginated scan history"""
    items: List[ScanHistoryItem]
    total: int
    page: int
    limit: int
    has_more: bool


class ScanDetail(BaseModel):
    """Schema for detailed scan view"""
    id: str
    message_text: str
    channel: str
    sender_info: Optional[str] = None
    
    # Results
    is_scam: bool
    confidence: float
    scam_type: Optional[str] = None
    risk_level: str
    
    # Full analysis
    analysis: Dict[str, Any] = {}
    indicators: List[str] = []
    recommendation: str = ""
    
    # Extracted data
    extracted_phones: List[str] = []
    extracted_emails: List[str] = []
    extracted_urls: List[str] = []
    extracted_upis: List[str] = []
    
    # User feedback
    user_feedback: Optional[str] = None
    
    # Metadata
    created_at: datetime
    auto_blocked: bool = False


class ScanFeedback(BaseModel):
    """Schema for providing feedback on scan result"""
    feedback: str = Field(..., pattern="^(correct|false_positive|false_negative)$")
    comment: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "false_positive",
                "comment": "This was a legitimate message from my bank"
            }
        }
