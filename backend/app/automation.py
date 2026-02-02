"""
automation.py

automated conversation management and intelligence gathering.
handles the complete lifecycle of scam engagement.
"""

from datetime import datetime, timedelta
from app.session_manager import Session
from app.scam_detector import detect_scam, analyze_conversation
from app.intelligence import extract_from_conversation, generate_agent_notes
from app.guvi_callback import send_final_result
from app.config import MIN_MESSAGES_BEFORE_REPORT, AUTO_CALLBACK


class ConversationAutomation:
    """
    automates conversation flow and callback decisions.
    
    handles:
    - when to escalate scam confidence
    - when to send callback
    - session cleanup
    """
    
    def __init__(self):
        self.callback_conditions = {
            "min_messages": MIN_MESSAGES_BEFORE_REPORT,
            "min_intel_items": 1,  # at least 1 piece of intel
            "max_messages": 20,    # force callback after this many
            "session_timeout_mins": 30  # cleanup old sessions
        }
    
    def should_send_callback(self, session: Session) -> bool:
        """
        decide if we should send callback now.
        multiple conditions checked.
        """
        
        if not AUTO_CALLBACK:
            return False
        
        if session.callback_sent:
            return False  # already sent
        
        if not session.scam_detected:
            return False  # not a scam
        
        msg_count = session.message_count
        
        # force callback after max messages
        if msg_count >= self.callback_conditions["max_messages"]:
            return True
        
        # minimum messages required
        if msg_count < self.callback_conditions["min_messages"]:
            return False
        
        # check if we have useful intel
        intel = session.intel
        intel_count = (
            len(intel.bank_accounts) +
            len(intel.upi_ids) +
            len(intel.phone_numbers) +
            len(intel.phishing_links)
        )
        
        if intel_count >= self.callback_conditions["min_intel_items"]:
            return True
        
        # if many messages but no intel, still send after threshold
        if msg_count >= self.callback_conditions["min_messages"] + 4:
            return True
        
        return False
    
    def process_callback(self, session: Session) -> dict:
        """
        prepare and send callback to guvi.
        """
        
        # get scam analysis
        scam_result = analyze_conversation(session.conversation)
        
        # extract final intel
        intel = extract_from_conversation(session.conversation)
        session.intel = intel
        
        # generate notes
        agent_notes = generate_agent_notes(intel, scam_result)
        
        # send callback
        result = send_final_result(
            session_id=session.session_id,
            scam_detected=session.scam_detected,
            total_messages=session.message_count,
            intel=intel,
            agent_notes=agent_notes
        )
        
        if result.get("success"):
            session.callback_sent = True
        
        return result
    
    def analyze_engagement_quality(self, session: Session) -> dict:
        """
        analyze how well we're engaging the scammer.
        used for internal metrics.
        """
        
        messages = session.conversation
        
        # count messages by sender
        scammer_msgs = [m for m in messages if m.get("sender") == "scammer"]
        user_msgs = [m for m in messages if m.get("sender") == "user"]
        
        # calculate response rate
        response_rate = len(user_msgs) / max(len(scammer_msgs), 1)
        
        # calculate intel extraction rate
        intel = session.intel
        intel_count = (
            len(intel.bank_accounts) +
            len(intel.upi_ids) +
            len(intel.phone_numbers) +
            len(intel.phishing_links)
        )
        intel_per_msg = intel_count / max(len(scammer_msgs), 1)
        
        # engagement score (0-100)
        score = min(100, (
            (response_rate * 30) +
            (intel_per_msg * 40) +
            (min(len(messages), 10) * 3)
        ))
        
        return {
            "total_messages": len(messages),
            "scammer_messages": len(scammer_msgs),
            "user_responses": len(user_msgs),
            "intel_extracted": intel_count,
            "engagement_score": round(score, 1),
            "callback_sent": session.callback_sent
        }
    
    def get_engagement_status(self, session: Session) -> str:
        """
        get human-readable engagement status.
        """
        
        if not session.scam_detected:
            return "monitoring"
        
        if session.callback_sent:
            return "completed"
        
        if session.message_count >= self.callback_conditions["min_messages"]:
            return "ready_for_callback"
        
        return "engaging"


# singleton
automation = ConversationAutomation()
