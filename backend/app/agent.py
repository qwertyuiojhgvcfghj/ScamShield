"""
agent.py

the brain of the honeypot - generates convincing responses to scammers.
supports multiple AI providers with automatic fallback.
detects language and responds in same language as scammer.
can answer factual questions using FREE APIs (DuckDuckGo, Wikipedia).

v3.5 features:
- uses fake victim identity for consistent persona
- applies emotional state modifiers
- uses scam-type-specific tactics
- knows when to send fake screenshots

the key is making responses feel human:
- short messages (not paragraphs)
- typos/grammar issues
- emotional reactions
- realistic delays in understanding
"""

import os
from app.ai_providers import generate_response, ai
from app.language_detector import detect_language, get_language_name
from app.factual_answers import is_factual_question, get_humanized_factual_answer

# load the persona prompt
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "agent_prompt.txt")

def load_system_prompt():
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # fallback if file missing
        return """You are a naive person who might fall for scams. 
        Keep scammer engaged, act confused, ask questions to extract info.
        Never reveal you know it's a scam. Keep responses short (1-2 sentences).
        IMPORTANT: Reply in the same language as the scammer."""


class HoneypotAgent:
    """
    AI agent that pretends to be a potential scam victim.
    
    Uses multiple AI providers with automatic fallback.
    Detects language and responds appropriately.
    """
    
    def __init__(self):
        self.system_prompt = load_system_prompt()
        self.providers = ai.get_available_providers()
        print(f"[AGENT] Initialized with providers: {self.providers}")
    
    def generate_response(self, conversation_history: str, latest_message: str, metadata: dict = None) -> str:
        """
        generate a response to scammer's message
        
        args:
            conversation_history: formatted string of previous messages
            latest_message: the new message from scammer
            metadata: optional context (channel, language, etc)
        
        returns:
            response string
        """
        
        # detect language from message
        detected_lang = detect_language(latest_message)
        lang_name = get_language_name(detected_lang)
        
        # use metadata language if provided and matches
        if metadata and metadata.get("language"):
            meta_lang = metadata["language"].lower()
            # map common language names to codes
            lang_map = {
                "english": "en", "hindi": "hi", "tamil": "ta",
                "telugu": "te", "kannada": "kn", "malayalam": "ml",
                "bengali": "bn", "marathi": "mr", "gujarati": "gu", "punjabi": "pa"
            }
            if meta_lang in lang_map:
                detected_lang = lang_map[meta_lang]
                lang_name = get_language_name(detected_lang)
        
        # CHECK: is this a factual question? use FREE APIs first
        if is_factual_question(latest_message):
            factual_answer = get_humanized_factual_answer(latest_message)
            if factual_answer:
                print(f"[AGENT] Using factual answer (FREE API)")
                return factual_answer
        
        # build the prompt with language instruction
        user_prompt = self._build_prompt(conversation_history, latest_message, metadata, lang_name)
        
        try:
            reply = generate_response(self.system_prompt, user_prompt)
            
            # cleanup - remove quotes if model wrapped response
            reply = reply.strip('"').strip("'")
            
            # sometimes model adds prefixes, remove them
            prefixes = ["you:", "reply:", "response:", "assistant:"]
            for prefix in prefixes:
                if reply.lower().startswith(prefix):
                    reply = reply[len(prefix):].strip()
            
            return reply
            
        except Exception as e:
            print(f"[ERROR] AI generation failed: {e}")
            return self._fallback_response(latest_message, detected_lang)
    
    def _build_prompt(self, history: str, message: str, metadata: dict, language: str) -> str:
        """construct the prompt for the model"""
        
        channel = metadata.get("channel", "SMS") if metadata else "SMS"
        
        # get victim identity from metadata
        victim_name = metadata.get("victim_name", "the victim") if metadata else "the victim"
        victim_age = metadata.get("victim_age", 45) if metadata else 45
        victim_occupation = metadata.get("victim_occupation", "homemaker") if metadata else "homemaker"
        
        # get emotional state from metadata
        emotional_state = metadata.get("emotional_state", "CONFUSED") if metadata else "CONFUSED"
        emotional_modifier = metadata.get("emotional_modifier", "") if metadata else ""
        
        # get scam type and tactics
        scam_type = metadata.get("scam_type", "UNKNOWN") if metadata else "UNKNOWN"
        tactics = metadata.get("recommended_tactics", []) if metadata else []
        tactics_str = ", ".join(tactics) if tactics else "ask questions, act confused"
        
        prompt = f"""You're chatting on {channel}. A scammer just sent you this message.

YOUR IDENTITY:
- Name: {victim_name}
- Age: {victim_age}
- Occupation: {victim_occupation}

CURRENT EMOTIONAL STATE: {emotional_state}
{emotional_modifier}

SCAM TYPE DETECTED: {scam_type}
RECOMMENDED TACTICS: {tactics_str}

IMPORTANT: The scammer is writing in {language}. You MUST reply in {language} only.

CONVERSATION SO FAR:
{history if history else "(This is the first message)"}

SCAMMER'S LATEST MESSAGE:
"{message}"

YOUR TASK:
Reply as {victim_name} in {language}. You are feeling {emotional_state.lower()}.
Keep it short (1-2 sentences) and realistic. Try to extract information.
Use tactics: {tactics_str}

YOUR REPLY (just the message in {language}, nothing else):"""
        
        return prompt
    
    def _fallback_response(self, message: str, lang: str = "en") -> str:
        """
        fallback responses when AI not available.
        returns response in detected language.
        """
        msg_lower = message.lower()
        
        # fallback responses in multiple languages
        responses = {
            "en": {
                "blocked": "Oh no! Which account sir? I have multiple banks",
                "otp": "Sir I didn't receive any OTP yet. Can you send again?",
                "upi": "Which UPI should I use? Paytm or PhonePe?",
                "link": "Link is not opening sir. Can you send again?",
                "won": "Really?? I never win anything! What should I do?",
                "police": "Please sir I am honest person! What happened?",
                "default": "I don't understand properly. Can you explain again please?"
            },
            "hi": {
                "blocked": "अरे बाप रे! कौन सा खाता सर? मेरे पास कई बैंक हैं",
                "otp": "सर मुझे अभी तक कोई OTP नहीं आया। फिर से भेज सकते हैं?",
                "upi": "कौन सा UPI use करूं? Paytm या PhonePe?",
                "link": "सर लिंक नहीं खुल रहा। फिर से भेजिए?",
                "won": "सच में?? मैं कभी नहीं जीतता! क्या करना होगा?",
                "police": "सर प्लीज मैं ईमानदार आदमी हूं! क्या हुआ?",
                "default": "मुझे ठीक से समझ नहीं आया। फिर से बताइए?"
            },
            "ta": {
                "blocked": "ஐயோ! எந்த அக்கவுண்ட் சார்? என்கிட்ட பல பேங்க் இருக்கு",
                "otp": "சார் எனக்கு இன்னும் OTP வரல. மறுபடியும் அனுப்புங்க?",
                "upi": "எந்த UPI use பண்ணணும்? Paytm அல்லது PhonePe?",
                "link": "சார் லிங்க் ஓபன் ஆகல. மறுபடியும் அனுப்புங்க?",
                "won": "உண்மையா?? நான் எப்பவும் ஜெயிக்க மாட்டேன்! என்ன பண்ணணும்?",
                "police": "சார் ப்ளீஸ் நான் நல்ல ஆள் தான்! என்ன ஆச்சு?",
                "default": "எனக்கு சரியா புரியல. மறுபடியும் சொல்லுங்க?"
            },
            "te": {
                "blocked": "అయ్యో! ఏ అకౌంట్ సర్? నా దగ్గర చాలా బ్యాంక్‌లు ఉన్నాయి",
                "otp": "సర్ నాకు ఇంకా OTP రాలేదు. మళ్ళీ పంపగలరా?",
                "upi": "ఏ UPI వాడాలి? Paytm లేదా PhonePe?",
                "link": "సర్ లింక్ ఓపెన్ కావడం లేదు. మళ్ళీ పంపండి?",
                "default": "నాకు సరిగ్గా అర్థం కాలేదు. మళ్ళీ చెప్పండి?"
            }
        }
        
        # get language responses, fallback to english
        lang_responses = responses.get(lang, responses["en"])
        
        # pick response based on keywords
        if any(w in msg_lower for w in ["blocked", "suspended", "closed", "ब्लॉक", "बंद"]):
            return lang_responses.get("blocked", lang_responses["default"])
        
        if any(w in msg_lower for w in ["otp", "code", "verify", "ओटीपी", "कोड"]):
            return lang_responses.get("otp", lang_responses["default"])
        
        if any(w in msg_lower for w in ["upi", "payment", "transfer", "send", "पैसे", "भेजो"]):
            return lang_responses.get("upi", lang_responses["default"])
        
        if any(w in msg_lower for w in ["click", "link", "website", "लिंक", "क्लिक"]):
            return lang_responses.get("link", lang_responses["default"])
        
        if any(w in msg_lower for w in ["won", "prize", "lottery", "जीत", "इनाम"]):
            return lang_responses.get("won", lang_responses["default"])
        
        if any(w in msg_lower for w in ["police", "legal", "arrest", "पुलिस", "कानूनी"]):
            return lang_responses.get("police", lang_responses["default"])
        
        return lang_responses["default"]


# singleton instance
agent = HoneypotAgent()


def get_agent_response(conversation_history: str, latest_message: str, metadata: dict = None) -> str:
    """convenience function to get response"""
    return agent.generate_response(conversation_history, latest_message, metadata)


# quick test
if __name__ == "__main__":
    test_msgs = [
        "Your bank account will be blocked in 24 hours! Call immediately!",
        "आपका खाता ब्लॉक हो जाएगा! तुरंत OTP भेजें!",
        "உங்கள் கணக்கு தடுக்கப்படும்! உடனடியாக அழைக்கவும்!"
    ]
    for msg in test_msgs:
        print(f"\nScammer: {msg}")
        print(f"Agent: {get_agent_response('', msg)}")
