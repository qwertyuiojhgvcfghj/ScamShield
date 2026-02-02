"""
time_metrics.py

tracks engagement metrics for each session.
measures how effectively we're wasting scammer's time.

metrics:
- total engagement time
- message count
- avg response time
- scammer frustration indicators
- api tokens saved (factual vs AI)
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class SessionMetrics:
    """engagement metrics for a session"""
    
    session_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # message counts
    scammer_messages: int = 0
    bot_messages: int = 0
    
    # response tracking
    response_times: List[float] = field(default_factory=list)  # seconds
    
    # API usage
    ai_calls: int = 0
    factual_api_calls: int = 0  # free API calls
    
    # engagement quality
    extracted_intel_count: int = 0
    scam_type: str = "UNKNOWN"
    frustration_score: int = 0  # 0-100
    
    def update_activity(self):
        """update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def add_scammer_message(self):
        """record a scammer message"""
        self.scammer_messages += 1
        self.update_activity()
    
    def add_bot_message(self, response_time_ms: float = 0, used_ai: bool = True):
        """record a bot response"""
        self.bot_messages += 1
        if response_time_ms > 0:
            self.response_times.append(response_time_ms / 1000)
        if used_ai:
            self.ai_calls += 1
        else:
            self.factual_api_calls += 1
        self.update_activity()
    
    def get_engagement_duration(self) -> timedelta:
        """get total engagement time"""
        return self.last_activity - self.start_time
    
    def get_engagement_seconds(self) -> int:
        """get engagement duration in seconds"""
        return int(self.get_engagement_duration().total_seconds())
    
    def get_engagement_formatted(self) -> str:
        """get human-readable engagement time"""
        duration = self.get_engagement_duration()
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            mins = total_seconds // 60
            secs = total_seconds % 60
            return f"{mins}m {secs}s"
        else:
            hours = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            return f"{hours}h {mins}m"
    
    def get_avg_response_time(self) -> float:
        """get average bot response time in seconds"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_tokens_saved(self) -> int:
        """estimate tokens saved by using free factual APIs"""
        # assume ~500 tokens per AI call saved
        return self.factual_api_calls * 500
    
    def get_api_cost_saved(self) -> float:
        """estimate money saved in USD (rough estimate)"""
        # rough estimate: $0.001 per 1K tokens
        tokens_saved = self.get_tokens_saved()
        return (tokens_saved / 1000) * 0.001
    
    def to_dict(self) -> Dict:
        """convert to dict for JSON response"""
        return {
            "session_id": self.session_id,
            "engagement": {
                "duration": self.get_engagement_formatted(),
                "duration_seconds": self.get_engagement_seconds(),
                "started": self.start_time.isoformat(),
                "last_activity": self.last_activity.isoformat(),
            },
            "messages": {
                "from_scammer": self.scammer_messages,
                "from_bot": self.bot_messages,
                "total": self.scammer_messages + self.bot_messages,
            },
            "performance": {
                "avg_response_time_sec": round(self.get_avg_response_time(), 2),
                "ai_api_calls": self.ai_calls,
                "free_api_calls": self.factual_api_calls,
                "tokens_saved": self.get_tokens_saved(),
                "cost_saved_usd": round(self.get_api_cost_saved(), 4),
            },
            "quality": {
                "intel_extracted": self.extracted_intel_count,
                "scam_type": self.scam_type,
                "frustration_score": self.frustration_score,
            }
        }
    
    def get_summary(self) -> str:
        """get human-readable summary"""
        return (
            f"Engaged scammer for {self.get_engagement_formatted()}, "
            f"exchanged {self.scammer_messages + self.bot_messages} messages, "
            f"extracted {self.extracted_intel_count} intel items, "
            f"saved ~{self.get_tokens_saved()} tokens"
        )


class MetricsTracker:
    """tracks metrics for all sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionMetrics] = {}
    
    def get_or_create(self, session_id: str) -> SessionMetrics:
        """get or create metrics for session"""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMetrics(session_id=session_id)
        return self._sessions[session_id]
    
    def get(self, session_id: str) -> Optional[SessionMetrics]:
        """get metrics for session"""
        return self._sessions.get(session_id)
    
    def record_scammer_message(self, session_id: str):
        """record incoming scammer message"""
        self.get_or_create(session_id).add_scammer_message()
    
    def record_bot_response(self, session_id: str, response_time_ms: float = 0, used_ai: bool = True):
        """record bot response"""
        self.get_or_create(session_id).add_bot_message(response_time_ms, used_ai)
    
    def update_intel_count(self, session_id: str, count: int):
        """update extracted intel count"""
        metrics = self.get_or_create(session_id)
        metrics.extracted_intel_count = count
    
    def set_scam_type(self, session_id: str, scam_type: str):
        """set the classified scam type"""
        self.get_or_create(session_id).scam_type = scam_type
    
    def get_global_stats(self) -> Dict:
        """get aggregate stats across all sessions"""
        if not self._sessions:
            return {"total_sessions": 0}
        
        total_engagement = sum(m.get_engagement_seconds() for m in self._sessions.values())
        total_messages = sum(m.scammer_messages + m.bot_messages for m in self._sessions.values())
        total_intel = sum(m.extracted_intel_count for m in self._sessions.values())
        total_tokens_saved = sum(m.get_tokens_saved() for m in self._sessions.values())
        
        return {
            "total_sessions": len(self._sessions),
            "total_engagement_seconds": total_engagement,
            "total_engagement_formatted": self._format_seconds(total_engagement),
            "total_messages": total_messages,
            "total_intel_extracted": total_intel,
            "total_tokens_saved": total_tokens_saved,
            "total_cost_saved_usd": round(sum(m.get_api_cost_saved() for m in self._sessions.values()), 4),
            "avg_engagement_seconds": total_engagement // max(len(self._sessions), 1),
        }
    
    def _format_seconds(self, seconds: int) -> str:
        """format seconds to human readable"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"
    
    def start_session(self, session_id: str):
        """start tracking a session"""
        self.get_or_create(session_id)
    
    def add_message(self, session_id: str, is_scammer: bool = True):
        """add a message to tracking"""
        if is_scammer:
            self.record_scammer_message(session_id)
        else:
            self.record_bot_response(session_id)
    
    def get_metrics(self, session_id: str) -> Optional[Dict]:
        """get metrics dict for a session"""
        metrics = self.get(session_id)
        return metrics.to_dict() if metrics else None
    
    def get_global_metrics(self) -> Dict:
        """get global metrics (alias for get_global_stats)"""
        return self.get_global_stats()


# singleton - both names work
metrics_tracker = MetricsTracker()
time_tracker = metrics_tracker  # alias for compatibility


def get_session_metrics(session_id: str) -> SessionMetrics:
    """convenience function"""
    return metrics_tracker.get_or_create(session_id)


def get_global_metrics() -> Dict:
    """get aggregate metrics"""
    return metrics_tracker.get_global_stats()


# test
if __name__ == "__main__":
    import time
    
    print("Testing metrics tracker...\n")
    
    # simulate a session
    session = get_session_metrics("test-session-1")
    
    # simulate conversation
    for i in range(5):
        session.add_scammer_message()
        time.sleep(0.1)  # simulate response time
        session.add_bot_message(response_time_ms=random.randint(100, 500), used_ai=(i % 2 == 0))
    
    session.extracted_intel_count = 3
    session.scam_type = "BANKING"
    
    print("Session metrics:")
    print(session.to_dict())
    print(f"\nSummary: {session.get_summary()}")
    
    print(f"\nGlobal stats: {get_global_metrics()}")
