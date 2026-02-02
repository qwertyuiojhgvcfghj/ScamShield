"""
scammer_fingerprint.py

tracks and identifies repeat scammers across sessions.
uses multiple data points to create unique fingerprints.

fingerprint elements:
- phone numbers
- upi ids
- email patterns
- language patterns
- timing patterns
- tactic patterns
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ScammerFingerprint:
    """unique fingerprint for a scammer"""
    
    fingerprint_id: str
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    # identifiers
    phone_numbers: Set[str] = field(default_factory=set)
    upi_ids: Set[str] = field(default_factory=set)
    email_addresses: Set[str] = field(default_factory=set)
    
    # patterns
    scam_types: Set[str] = field(default_factory=set)
    languages_used: Set[str] = field(default_factory=set)
    
    # sessions
    session_ids: List[str] = field(default_factory=list)
    
    # stats
    total_messages: int = 0
    total_engagement_seconds: int = 0
    
    def update(self, session_id: str, intel: dict = None, scam_type: str = None, language: str = None):
        """update fingerprint with new session data"""
        self.last_seen = datetime.utcnow()
        
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)
        
        if intel:
            if intel.get("phoneNumbers"):
                self.phone_numbers.update(intel["phoneNumbers"])
            if intel.get("upiIds"):
                self.upi_ids.update(intel["upiIds"])
            if intel.get("emailAddresses"):
                self.email_addresses.update(intel["emailAddresses"])
        
        if scam_type:
            self.scam_types.add(scam_type)
        
        if language:
            self.languages_used.add(language)
    
    def is_repeat_offender(self) -> bool:
        """check if this is a repeat scammer"""
        return len(self.session_ids) > 1
    
    def get_session_count(self) -> int:
        return len(self.session_ids)
    
    def to_dict(self) -> Dict:
        return {
            "fingerprint_id": self.fingerprint_id,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "is_repeat_offender": self.is_repeat_offender(),
            "session_count": self.get_session_count(),
            "identifiers": {
                "phone_numbers": list(self.phone_numbers),
                "upi_ids": list(self.upi_ids),
                "email_addresses": list(self.email_addresses),
            },
            "patterns": {
                "scam_types": list(self.scam_types),
                "languages": list(self.languages_used),
            },
            "stats": {
                "total_messages": self.total_messages,
                "total_engagement_seconds": self.total_engagement_seconds,
            }
        }


class FingerprintTracker:
    """tracks scammer fingerprints across sessions"""
    
    def __init__(self):
        # fingerprint_id -> ScammerFingerprint
        self._fingerprints: Dict[str, ScammerFingerprint] = {}
        
        # quick lookup: phone/upi/email -> fingerprint_id
        self._phone_index: Dict[str, str] = {}
        self._upi_index: Dict[str, str] = {}
        self._email_index: Dict[str, str] = {}
    
    def _generate_fingerprint_id(self, *identifiers) -> str:
        """generate unique fingerprint ID from identifiers"""
        combined = "|".join(sorted([str(i).lower() for i in identifiers if i]))
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def find_or_create(self, intel: dict) -> Optional[ScammerFingerprint]:
        """find existing fingerprint or create new one based on intel"""
        
        phones = intel.get("phoneNumbers", [])
        upis = intel.get("upiIds", [])
        emails = intel.get("emailAddresses", [])
        
        # try to find existing fingerprint
        fingerprint_id = None
        
        for phone in phones:
            if phone in self._phone_index:
                fingerprint_id = self._phone_index[phone]
                break
        
        if not fingerprint_id:
            for upi in upis:
                if upi in self._upi_index:
                    fingerprint_id = self._upi_index[upi]
                    break
        
        if not fingerprint_id:
            for email in emails:
                if email in self._email_index:
                    fingerprint_id = self._email_index[email]
                    break
        
        # found existing
        if fingerprint_id and fingerprint_id in self._fingerprints:
            return self._fingerprints[fingerprint_id]
        
        # no identifiers to track
        if not phones and not upis and not emails:
            return None
        
        # create new fingerprint
        fingerprint_id = self._generate_fingerprint_id(
            phones[0] if phones else None,
            upis[0] if upis else None,
            emails[0] if emails else None
        )
        
        fingerprint = ScammerFingerprint(fingerprint_id=fingerprint_id)
        self._fingerprints[fingerprint_id] = fingerprint
        
        # index all identifiers
        for phone in phones:
            self._phone_index[phone] = fingerprint_id
        for upi in upis:
            self._upi_index[upi] = fingerprint_id
        for email in emails:
            self._email_index[email] = fingerprint_id
        
        return fingerprint
    
    def track(self, session_id: str, intel: dict, scam_type: str = None, language: str = None) -> Optional[ScammerFingerprint]:
        """track a scammer from session intel"""
        fingerprint = self.find_or_create(intel)
        
        if fingerprint:
            fingerprint.update(session_id, intel, scam_type, language)
            
            # update indexes with any new identifiers
            for phone in intel.get("phoneNumbers", []):
                self._phone_index[phone] = fingerprint.fingerprint_id
            for upi in intel.get("upiIds", []):
                self._upi_index[upi] = fingerprint.fingerprint_id
            for email in intel.get("emailAddresses", []):
                self._email_index[email] = fingerprint.fingerprint_id
        
        return fingerprint
    
    def get_fingerprint(self, fingerprint_id: str) -> Optional[ScammerFingerprint]:
        return self._fingerprints.get(fingerprint_id)
    
    def find_by_phone(self, phone: str) -> Optional[ScammerFingerprint]:
        fp_id = self._phone_index.get(phone)
        return self._fingerprints.get(fp_id) if fp_id else None
    
    def find_by_upi(self, upi: str) -> Optional[ScammerFingerprint]:
        fp_id = self._upi_index.get(upi)
        return self._fingerprints.get(fp_id) if fp_id else None
    
    def get_repeat_offenders(self) -> List[ScammerFingerprint]:
        """get all repeat offenders"""
        return [fp for fp in self._fingerprints.values() if fp.is_repeat_offender()]
    
    def get_stats(self) -> Dict:
        """get overall fingerprinting stats"""
        total = len(self._fingerprints)
        repeat = len(self.get_repeat_offenders())
        
        return {
            "total_scammers_tracked": total,
            "repeat_offenders": repeat,
            "unique_phones": len(self._phone_index),
            "unique_upis": len(self._upi_index),
            "unique_emails": len(self._email_index),
        }
    
    def check_fingerprint(self, intel: dict) -> Dict:
        """check if this intel matches a known scammer"""
        fingerprint = self.find_or_create(intel)
        
        if fingerprint and fingerprint.get_session_count() > 0:
            return {
                "is_known": fingerprint.is_repeat_offender(),
                "fingerprint_id": fingerprint.fingerprint_id,
                "session_count": fingerprint.get_session_count(),
                "first_seen": fingerprint.first_seen.isoformat(),
                "patterns": {
                    "scam_types": list(fingerprint.scam_types),
                    "languages": list(fingerprint.languages_used),
                }
            }
        
        return {"is_known": False}
    
    def add_or_update_scammer(self, intel: dict, session_id: str, scam_type: str = None):
        """add or update scammer fingerprint"""
        return self.track(session_id, intel, scam_type)
    
    def get_known_scammers(self) -> List[Dict]:
        """get all known scammers as list of dicts"""
        return [fp.to_dict() for fp in self._fingerprints.values()]


# singleton
fingerprint_tracker = FingerprintTracker()
scammer_db = fingerprint_tracker  # alias for compatibility


def track_scammer(session_id: str, intel: dict, scam_type: str = None, language: str = None) -> Optional[ScammerFingerprint]:
    """convenience function to track scammer"""
    return fingerprint_tracker.track(session_id, intel, scam_type, language)


def find_scammer_by_phone(phone: str) -> Optional[ScammerFingerprint]:
    return fingerprint_tracker.find_by_phone(phone)


def find_scammer_by_upi(upi: str) -> Optional[ScammerFingerprint]:
    return fingerprint_tracker.find_by_upi(upi)


def get_fingerprint_stats() -> Dict:
    return fingerprint_tracker.get_stats()


# test
if __name__ == "__main__":
    print("Testing scammer fingerprinting...\n")
    
    # simulate sessions from same scammer
    intel1 = {
        "phoneNumbers": ["+919876543210"],
        "upiIds": ["scammer@ybl"],
    }
    
    intel2 = {
        "phoneNumbers": ["+919876543210", "+919876543211"],  # same scammer, new number
        "upiIds": ["scammer2@paytm"],
    }
    
    intel3 = {
        "phoneNumbers": ["+919999999999"],  # different scammer
        "upiIds": ["other@ybl"],
    }
    
    fp1 = track_scammer("session-1", intel1, "BANKING", "en")
    print(f"Session 1: {fp1.fingerprint_id} (sessions: {fp1.get_session_count()})")
    
    fp2 = track_scammer("session-2", intel2, "BANKING", "hi")
    print(f"Session 2: {fp2.fingerprint_id} (sessions: {fp2.get_session_count()})")
    print(f"  Same scammer? {fp1.fingerprint_id == fp2.fingerprint_id}")
    print(f"  Repeat offender? {fp2.is_repeat_offender()}")
    
    fp3 = track_scammer("session-3", intel3, "LOTTERY", "en")
    print(f"Session 3: {fp3.fingerprint_id} (sessions: {fp3.get_session_count()})")
    print(f"  Same as session 1? {fp1.fingerprint_id == fp3.fingerprint_id}")
    
    print(f"\nStats: {get_fingerprint_stats()}")
