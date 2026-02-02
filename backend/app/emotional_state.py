"""
emotional_state.py

simulates emotional states to make honeypot more believable.
transitions through realistic emotional responses.

states:
- CONFUSED: initial state, doesn't understand
- CONCERNED: starting to worry
- SCARED: afraid of consequences
- COMPLIANT: willing to help
- HESITANT: having second thoughts
- SUSPICIOUS: starting to doubt
- PANICKED: extreme fear/urgency
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class EmotionalState(Enum):
    CONFUSED = "confused"
    CONCERNED = "concerned"
    SCARED = "scared"
    COMPLIANT = "compliant"
    HESITANT = "hesitant"
    SUSPICIOUS = "suspicious"
    PANICKED = "panicked"


# state transition probabilities based on scammer tactics
STATE_TRANSITIONS = {
    EmotionalState.CONFUSED: {
        "threat": (EmotionalState.SCARED, 0.7),
        "urgency": (EmotionalState.CONCERNED, 0.6),
        "authority": (EmotionalState.CONCERNED, 0.5),
        "help": (EmotionalState.COMPLIANT, 0.4),
        "default": (EmotionalState.CONFUSED, 0.8),
    },
    EmotionalState.CONCERNED: {
        "threat": (EmotionalState.SCARED, 0.8),
        "urgency": (EmotionalState.PANICKED, 0.3),
        "reassure": (EmotionalState.COMPLIANT, 0.6),
        "help": (EmotionalState.COMPLIANT, 0.7),
        "default": (EmotionalState.CONCERNED, 0.6),
    },
    EmotionalState.SCARED: {
        "threat": (EmotionalState.PANICKED, 0.5),
        "reassure": (EmotionalState.COMPLIANT, 0.7),
        "help": (EmotionalState.COMPLIANT, 0.8),
        "pressure": (EmotionalState.HESITANT, 0.4),
        "default": (EmotionalState.SCARED, 0.6),
    },
    EmotionalState.COMPLIANT: {
        "pressure": (EmotionalState.HESITANT, 0.5),
        "threat": (EmotionalState.SCARED, 0.4),
        "reassure": (EmotionalState.COMPLIANT, 0.8),
        "default": (EmotionalState.COMPLIANT, 0.7),
    },
    EmotionalState.HESITANT: {
        "threat": (EmotionalState.SCARED, 0.6),
        "pressure": (EmotionalState.SUSPICIOUS, 0.5),
        "reassure": (EmotionalState.COMPLIANT, 0.5),
        "default": (EmotionalState.HESITANT, 0.6),
    },
    EmotionalState.SUSPICIOUS: {
        "threat": (EmotionalState.SCARED, 0.4),
        "reassure": (EmotionalState.HESITANT, 0.5),
        "default": (EmotionalState.SUSPICIOUS, 0.7),
    },
    EmotionalState.PANICKED: {
        "reassure": (EmotionalState.SCARED, 0.6),
        "help": (EmotionalState.COMPLIANT, 0.5),
        "default": (EmotionalState.PANICKED, 0.5),
    },
}

# emotional response templates
EMOTIONAL_RESPONSES = {
    EmotionalState.CONFUSED: {
        "en": [
            "Wait, I don't understand... can you explain again?",
            "Sorry, what are you saying? I'm confused.",
            "I don't get it... what should I do?",
            "Huh? What is happening? Please explain slowly.",
        ],
        "hi": [
            "रुकिए, मुझे समझ नहीं आया... फिर से बताइए?",
            "माफ कीजिए, आप क्या कह रहे हैं? मुझे confusion हो रहा है",
            "मुझे समझ नहीं आ रहा... क्या करना है?",
        ],
    },
    EmotionalState.CONCERNED: {
        "en": [
            "Oh no, is there really a problem? What happened?",
            "This is concerning... what should I do?",
            "I'm worried now... please tell me more.",
            "Is this serious? What's wrong with my account?",
        ],
        "hi": [
            "अरे नहीं, सच में कोई problem है? क्या हुआ?",
            "मुझे चिंता हो रही है... क्या करना चाहिए?",
            "ये serious है क्या? मेरे account में क्या गड़बड़ है?",
        ],
    },
    EmotionalState.SCARED: {
        "en": [
            "Oh my god! Please don't block my account! I'll do anything!",
            "Please sir, I'm scared! What do I do?",
            "I don't want any trouble! Please help me!",
            "I'm very worried now... please tell me what to do!",
        ],
        "hi": [
            "भगवान! प्लीज मेरा account block मत करिए! मैं कुछ भी करूंगा!",
            "सर प्लीज, मुझे डर लग रहा है! क्या करूं?",
            "मुझे कोई problem नहीं चाहिए! प्लीज मदद करिए!",
        ],
    },
    EmotionalState.COMPLIANT: {
        "en": [
            "Okay okay, I'll do whatever you say. Just tell me.",
            "Yes sir, I'm ready to help. What do you need?",
            "Fine, I trust you. Tell me what to do.",
            "Alright, I'll cooperate. Please guide me.",
        ],
        "hi": [
            "ठीक है ठीक है, आप जो कहो मैं करूंगा। बस बताइए।",
            "हाँ सर, मैं तैयार हूं। क्या चाहिए आपको?",
            "चलिए, मुझे भरोसा है। बताइए क्या करना है।",
        ],
    },
    EmotionalState.HESITANT: {
        "en": [
            "Wait, are you sure about this? Let me think...",
            "I'm not sure... maybe I should check with someone first.",
            "Hmm, something doesn't feel right... can you verify again?",
            "Hold on, let me just confirm this with my bank first.",
        ],
        "hi": [
            "रुकिए, आप sure हैं? मुझे सोचने दीजिए...",
            "मुझे पक्का नहीं है... शायद पहले किसी से पूछ लूं।",
            "हम्म, कुछ ठीक नहीं लग रहा... फिर से verify करिए?",
        ],
    },
    EmotionalState.SUSPICIOUS: {
        "en": [
            "Wait a minute... how do I know you're really from the bank?",
            "Something is fishy here... can you give me your employee ID?",
            "I think I should call my bank directly to verify this.",
            "Why are you asking for OTP? Bank never asks for OTP on call.",
        ],
        "hi": [
            "एक मिनट... मुझे कैसे पता आप सच में बैंक से हैं?",
            "कुछ गड़बड़ लग रहा है... अपना employee ID दीजिए?",
            "मुझे लगता है मैं bank को directly call करके verify करूं।",
        ],
    },
    EmotionalState.PANICKED: {
        "en": [
            "OH NO OH NO! Please don't do anything! I'll send immediately!",
            "Please please please! Don't arrest me! I'll do everything!",
            "I'm so scared! Just tell me quickly what to do!",
            "My hands are shaking! Please help me fix this NOW!",
        ],
        "hi": [
            "अरे बाप रे! प्लीज कुछ मत करिए! मैं अभी भेजता हूं!",
            "प्लीज प्लीज! मुझे arrest मत करिए! सब करूंगा!",
            "मुझे बहुत डर लग रहा है! जल्दी बताइए क्या करना है!",
        ],
    },
}

# scammer tactic detection keywords
TACTIC_KEYWORDS = {
    "threat": ["block", "arrest", "police", "legal", "suspend", "cancel", "jail", 
               "ब्लॉक", "गिरफ्तार", "पुलिस", "बंद"],
    "urgency": ["immediately", "now", "urgent", "hurry", "today", "quickly", "fast",
                "तुरंत", "अभी", "जल्दी"],
    "authority": ["bank", "rbi", "government", "officer", "manager", "department",
                  "बैंक", "सरकार", "अधिकारी"],
    "pressure": ["last chance", "final", "deadline", "expire", "must", "have to",
                 "आखिरी", "ज़रूरी"],
    "reassure": ["don't worry", "safe", "help", "trust", "secure", "protect",
                 "चिंता मत", "सुरक्षित"],
    "help": ["help", "assist", "support", "solve", "fix", "resolve",
             "मदद", "सहायता"],
}


@dataclass
class EmotionalContext:
    """tracks emotional state for a session"""
    
    session_id: str
    current_state: EmotionalState = EmotionalState.CONFUSED
    state_history: List[EmotionalState] = None
    transition_count: int = 0
    
    def __post_init__(self):
        if self.state_history is None:
            self.state_history = [self.current_state]
    
    def detect_tactic(self, message: str) -> str:
        """detect scammer tactic from message"""
        msg_lower = message.lower()
        
        for tactic, keywords in TACTIC_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                return tactic
        
        return "default"
    
    def transition(self, message: str) -> EmotionalState:
        """transition to new state based on message"""
        tactic = self.detect_tactic(message)
        transitions = STATE_TRANSITIONS.get(self.current_state, {})
        
        if tactic in transitions:
            new_state, probability = transitions[tactic]
        else:
            new_state, probability = transitions.get("default", (self.current_state, 0.5))
        
        # random chance of transition
        if random.random() < probability:
            self.current_state = new_state
            self.state_history.append(new_state)
            self.transition_count += 1
        
        return self.current_state
    
    def get_emotional_response(self, language: str = "en") -> str:
        """get response appropriate for current emotional state"""
        responses = EMOTIONAL_RESPONSES.get(self.current_state, {})
        lang_responses = responses.get(language, responses.get("en", ["..."]))
        return random.choice(lang_responses)
    
    def get_state_modifier(self) -> str:
        """get modifier to add to AI prompt based on state"""
        modifiers = {
            EmotionalState.CONFUSED: "You are confused and don't understand what's happening.",
            EmotionalState.CONCERNED: "You are concerned and worried about the situation.",
            EmotionalState.SCARED: "You are scared and afraid of the consequences.",
            EmotionalState.COMPLIANT: "You are willing to help and follow instructions.",
            EmotionalState.HESITANT: "You are having second thoughts and are unsure.",
            EmotionalState.SUSPICIOUS: "You are becoming suspicious and asking questions.",
            EmotionalState.PANICKED: "You are in a state of panic and will do anything.",
        }
        return modifiers.get(self.current_state, "")


class EmotionalStateManager:
    """manages emotional states for all sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, EmotionalContext] = {}
    
    def get_or_create(self, session_id: str) -> EmotionalContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = EmotionalContext(session_id=session_id)
        return self._sessions[session_id]
    
    def process_message(self, session_id: str, message: str) -> EmotionalContext:
        """process message and update emotional state"""
        context = self.get_or_create(session_id)
        context.transition(message)
        return context
    
    def get_current_state(self, session_id: str) -> EmotionalState:
        return self.get_or_create(session_id).current_state


# singleton
emotion_manager = EmotionalStateManager()


def get_emotional_context(session_id: str) -> EmotionalContext:
    return emotion_manager.get_or_create(session_id)


def process_emotion(session_id: str, message: str) -> EmotionalContext:
    return emotion_manager.process_message(session_id, message)


# test
if __name__ == "__main__":
    print("Testing emotional state machine...\n")
    
    messages = [
        "Hello, this is from SBI bank.",
        "Your account will be blocked immediately!",
        "Please share OTP to verify.",
        "Don't worry, we are here to help you.",
        "If you don't share now, police will arrest you!",
        "This is your last chance, hurry!",
    ]
    
    ctx = get_emotional_context("test-session")
    
    for msg in messages:
        ctx = process_emotion("test-session", msg)
        print(f"Scammer: {msg[:40]}...")
        print(f"  State: {ctx.current_state.value}")
        print(f"  Response: {ctx.get_emotional_response()}")
        print()
