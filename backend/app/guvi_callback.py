"""
guvi_callback.py

sends the final extracted intelligence to guvi's evaluation endpoint.
this is MANDATORY for the hackathon - they use this to score our solution.

endpoint: POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
"""

import requests
from app.config import GUVI_CALLBACK_URL
from app.intelligence import ExtractedIntel


def send_final_result(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    intel: ExtractedIntel,
    agent_notes: str
) -> dict:
    """
    send intelligence report to guvi
    
    args:
        session_id: unique session identifier
        scam_detected: whether scam was confirmed
        total_messages: number of messages in conversation
        intel: extracted intelligence object
        agent_notes: summary of scammer behavior
    
    returns:
        dict with success status and response
    """
    
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": intel.to_dict(),
        "agentNotes": agent_notes
    }
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"[CALLBACK] Sent to GUVI - Status: {response.status_code}")
        print(f"[CALLBACK] Payload: {payload}")
        
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response": response.text
        }
        
    except requests.Timeout:
        print(f"[ERROR] GUVI callback timeout")
        return {"success": False, "error": "timeout"}
    
    except requests.RequestException as e:
        print(f"[ERROR] GUVI callback failed: {e}")
        return {"success": False, "error": str(e)}


def should_send_callback(session) -> bool:
    """
    decide if we should send callback now.
    
    conditions:
    - scam was detected
    - enough messages exchanged (got sufficient intel)
    - callback not already sent
    """
    from app.config import MIN_MESSAGES_BEFORE_REPORT
    
    if session.callback_sent:
        return False  # already sent
    
    if not session.scam_detected:
        return False  # not a scam
    
    if session.message_count < MIN_MESSAGES_BEFORE_REPORT:
        return False  # need more engagement
    
    # check if we have any useful intel
    if session.intel.is_empty():
        # no intel yet, but if msg count is high, send anyway
        if session.message_count >= MIN_MESSAGES_BEFORE_REPORT + 4:
            return True
        return False
    
    return True
