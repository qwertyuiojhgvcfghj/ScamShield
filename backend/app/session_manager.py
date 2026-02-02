"""
session_manager.py

keeps track of conversations by session id.
using in-memory dict for now - works fine for hackathon demo.
for production would swap this with redis or something.

each session stores:
- conversation history
- scam detection status
- extracted intel
- message count
- whether we already sent callback to guvi
"""

from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field
from app.intelligence import ExtractedIntel


@dataclass
class Session:
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    conversation: list = field(default_factory=list)
    scam_detected: bool = False
    scam_confidence: float = 0.0
    intel: ExtractedIntel = field(default_factory=ExtractedIntel)
    callback_sent: bool = False  # track if we already reported to guvi
    
    @property
    def message_count(self):
        return len(self.conversation)
    
    def add_message(self, sender: str, text: str, timestamp: str = None):
        """add a message to conversation history"""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        self.conversation.append({
            "sender": sender,
            "text": text,
            "timestamp": timestamp
        })
    
    def get_history_for_prompt(self, max_messages: int = 20):
        """
        format conversation for llm prompt
        only take last N messages to avoid token limit issues
        """
        recent = self.conversation[-max_messages:]
        
        formatted = []
        for msg in recent:
            role = "Scammer" if msg["sender"] == "scammer" else "You"
            formatted.append(f"{role}: {msg['text']}")
        
        return "\n".join(formatted)


class SessionManager:
    """
    simple in-memory session store
    
    note: data lost on server restart! 
    fine for hackathon, not for production
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def get_or_create(self, session_id: str) -> Session:
        """get existing session or create new one"""
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        return self._sessions[session_id]
    
    def get(self, session_id: str) -> Optional[Session]:
        """get session if exists"""
        return self._sessions.get(session_id)
    
    def delete(self, session_id: str):
        """remove session (cleanup after callback)"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def list_sessions(self):
        """list all active session ids - useful for debugging"""
        return list(self._sessions.keys())
    
    def stats(self):
        """basic stats about active sessions"""
        return {
            "total_sessions": len(self._sessions),
            "scam_sessions": sum(1 for s in self._sessions.values() if s.scam_detected),
            "callbacks_sent": sum(1 for s in self._sessions.values() if s.callback_sent)
        }


# global instance - imported by other modules
session_store = SessionManager()
