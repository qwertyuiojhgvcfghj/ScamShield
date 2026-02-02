"""
session_service.py - Honeypot session management (migrated from in-memory)

This replaces the in-memory session_manager.py with MongoDB persistence.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.db.models.session import HoneypotSession, SessionStatus
from app.db.models.scammer import ScammerFingerprint
from app.core.security import create_scammer_fingerprint_hash


class SessionService:
    """
    Service for honeypot session management.
    Replaces the in-memory SessionManager.
    """
    
    @staticmethod
    async def get_or_create_session(session_id: str) -> HoneypotSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: External session identifier
            
        Returns:
            HoneypotSession document
        """
        session = await HoneypotSession.find_one(
            HoneypotSession.session_id == session_id
        )
        
        if not session:
            session = HoneypotSession(session_id=session_id)
            await session.insert()
        
        return session
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[HoneypotSession]:
        """
        Get session if exists.
        """
        return await HoneypotSession.find_one(
            HoneypotSession.session_id == session_id
        )
    
    @staticmethod
    async def add_message(
        session_id: str,
        sender: str,
        text: str,
        timestamp: str = None,
        metadata: dict = None
    ) -> HoneypotSession:
        """
        Add a message to session conversation.
        """
        session = await SessionService.get_or_create_session(session_id)
        session.add_message(sender, text, timestamp, metadata)
        await session.save()
        return session
    
    @staticmethod
    async def update_scam_info(
        session_id: str,
        scam_type: str,
        confidence: float
    ) -> Optional[HoneypotSession]:
        """
        Update scam classification for session.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        session.scam_type = scam_type
        session.scam_confidence = confidence
        session.updated_at = datetime.utcnow()
        await session.save()
        return session
    
    @staticmethod
    async def add_intel(
        session_id: str,
        intel_type: str,
        value: str
    ) -> Optional[HoneypotSession]:
        """
        Add extracted intelligence to session.
        
        Args:
            session_id: Session identifier
            intel_type: Type of intel (phones, emails, bank_accounts, upi_ids, etc.)
            value: The extracted value
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        session.add_intel(intel_type, value)
        await session.save()
        return session
    
    @staticmethod
    async def update_intel_batch(
        session_id: str,
        intel_data: Dict[str, List[str]]
    ) -> Optional[HoneypotSession]:
        """
        Update intel with multiple values at once.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        for intel_type, values in intel_data.items():
            for value in values:
                session.add_intel(intel_type, value)
        
        await session.save()
        return session
    
    @staticmethod
    async def update_emotional_state(
        session_id: str,
        state: str
    ) -> Optional[HoneypotSession]:
        """
        Update emotional state for session.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        session.emotional_state = state
        session.updated_at = datetime.utcnow()
        await session.save()
        return session
    
    @staticmethod
    async def update_metadata(
        session_id: str,
        channel: str = None,
        language: str = None,
        locale: str = None
    ) -> Optional[HoneypotSession]:
        """
        Update session metadata.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        if channel:
            session.channel = channel
        if language:
            session.language = language
        if locale:
            session.locale = locale
        
        session.updated_at = datetime.utcnow()
        await session.save()
        return session
    
    @staticmethod
    async def mark_callback_sent(
        session_id: str,
        response: Dict[str, Any] = None
    ) -> Optional[HoneypotSession]:
        """
        Mark that callback has been sent for session.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        session.callback_sent = True
        session.callback_response = response
        await session.save()
        return session
    
    @staticmethod
    async def close_session(session_id: str) -> Optional[HoneypotSession]:
        """
        Close a session.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        await session.close_session()
        
        # Link to scammer fingerprint if we have intel
        await SessionService._link_to_scammer(session)
        
        return session
    
    @staticmethod
    async def get_session_transcript(session_id: str) -> Optional[List[Dict]]:
        """
        Get full conversation transcript.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return None
        
        return session.messages
    
    @staticmethod
    async def get_history_for_prompt(
        session_id: str,
        max_messages: int = 20
    ) -> str:
        """
        Get formatted conversation history for LLM prompt.
        """
        session = await SessionService.get_session(session_id)
        if not session:
            return ""
        
        return session.get_history_for_prompt(max_messages)
    
    @staticmethod
    async def list_sessions(
        status: SessionStatus = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[HoneypotSession]:
        """
        List sessions with optional filtering.
        """
        query = HoneypotSession.find()
        
        if status:
            query = query.find(HoneypotSession.status == status)
        
        return await query.sort(-HoneypotSession.created_at).skip(skip).limit(limit).to_list()
    
    @staticmethod
    async def get_active_session_count() -> int:
        """
        Get count of active sessions.
        """
        return await HoneypotSession.find(
            HoneypotSession.status == SessionStatus.ACTIVE
        ).count()
    
    @staticmethod
    async def _link_to_scammer(session: HoneypotSession):
        """
        Link session to scammer fingerprint (or create new one).
        """
        # Collect all identifiers
        identifiers = []
        identifiers.extend(session.intel.get("phones", []))
        identifiers.extend(session.intel.get("emails", []))
        identifiers.extend(session.intel.get("upi_ids", []))
        
        if not identifiers:
            return  # No identifiers to fingerprint
        
        # Try to find existing scammer
        scammer = None
        for identifier in identifiers:
            scammer = await ScammerFingerprint.find_by_identifier(identifier)
            if scammer:
                break
        
        if scammer:
            # Update existing scammer
            scammer.add_session(session.session_id)
            
            for phone in session.intel.get("phones", []):
                scammer.add_identifier("phone", phone)
            for email in session.intel.get("emails", []):
                scammer.add_identifier("email", email)
            for upi in session.intel.get("upi_ids", []):
                scammer.add_identifier("upi", upi)
            for bank in session.intel.get("bank_accounts", []):
                scammer.add_identifier("bank", bank)
            
            if session.scam_type and session.scam_type not in scammer.scam_types:
                scammer.scam_types.append(session.scam_type)
            
            await scammer.save()
        else:
            # Create new scammer fingerprint
            fingerprint_hash = create_scammer_fingerprint_hash(identifiers)
            
            scammer = ScammerFingerprint(
                fingerprint_hash=fingerprint_hash,
                phone_numbers=session.intel.get("phones", []),
                email_addresses=session.intel.get("emails", []),
                bank_accounts=session.intel.get("bank_accounts", []),
                upi_ids=session.intel.get("upi_ids", []),
                session_ids=[session.session_id],
                total_sessions=1,
                scam_types=[session.scam_type] if session.scam_type else [],
            )
            await scammer.insert()
        
        # Link session to scammer
        session.scammer_fingerprint_id = str(scammer.id)
        await session.save()


# Create a compatibility layer for existing code
class SessionManagerCompat:
    """
    Compatibility wrapper to make SessionService work like the old SessionManager.
    This allows gradual migration without breaking existing code.
    """
    
    async def get_or_create(self, session_id: str) -> HoneypotSession:
        return await SessionService.get_or_create_session(session_id)
    
    async def get(self, session_id: str) -> Optional[HoneypotSession]:
        return await SessionService.get_session(session_id)


# For backward compatibility
session_store_async = SessionManagerCompat()
