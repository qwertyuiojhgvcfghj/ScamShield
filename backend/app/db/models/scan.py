"""
scan.py - Scan request document
"""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, Dict, Any, List, Annotated
from datetime import datetime
from enum import Enum


class Channel(str, Enum):
    SMS = "SMS"
    EMAIL = "Email"
    WHATSAPP = "WhatsApp"
    TELEGRAM = "Telegram"
    OTHER = "Other"


class ScanRequest(Document):
    """
    Record of a message scan request and result.
    """
    user_id: Annotated[str, Indexed()]  # References User._id
    
    # Input
    message_text: str
    channel: Channel = Channel.SMS
    sender_info: Optional[str] = None  # Phone/email of sender if provided
    
    # Results
    is_scam: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    scam_type: Optional[str] = None  # phishing, lottery, tech_support, etc.
    
    # Detailed analysis
    analysis: Dict[str, Any] = Field(default_factory=dict)
    # Example: {"indicators": ["urgency", "money_request"], "risk_factors": [...]}
    
    # Extracted entities
    extracted_phones: List[str] = Field(default_factory=list)
    extracted_emails: List[str] = Field(default_factory=list)
    extracted_urls: List[str] = Field(default_factory=list)
    extracted_upis: List[str] = Field(default_factory=list)
    
    # Status
    auto_blocked: bool = False
    user_feedback: Optional[str] = None  # "correct", "false_positive", "false_negative"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "scan_requests"
        indexes = [
            [("user_id", 1), ("created_at", -1)],  # For user history queries
            [("is_scam", 1), ("created_at", -1)],  # For analytics
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "message_text": "Congratulations! You won $1000000. Click here to claim.",
                "channel": "SMS",
                "is_scam": True,
                "confidence": 0.95,
                "scam_type": "lottery"
            }
        }
    
    def get_preview(self, max_length: int = 100) -> str:
        """Get truncated preview of message"""
        if len(self.message_text) <= max_length:
            return self.message_text
        return self.message_text[:max_length] + "..."
