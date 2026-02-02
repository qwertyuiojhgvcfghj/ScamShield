"""
smart_tactics.py

advanced tactics for extracting maximum information from scammers.
uses psychological techniques and social engineering reverse.

tactics:
- delay tactics (pretend confusion, slow responses)
- trust building (gradual compliance)
- information extraction (subtle questions)
- counter social engineering
- fake compliance with data collection
"""

import random
from typing import Dict, List, Optional
from datetime import datetime


class SmartTactics:
    """
    intelligent tactics engine for maximum data extraction
    """
    
    def __init__(self):
        self.conversation_stage = {}  # session_id -> stage
        self.extracted_data = {}       # session_id -> data
        
        # conversation stages
        self.stages = [
            "initial_confusion",      # pretend not to understand
            "building_trust",         # show slight interest
            "fake_compliance",        # agree to help
            "information_gathering",  # ask questions subtly
            "delay_tactics",          # stall for more info
            "final_extraction"        # get remaining details
        ]
    
    def get_current_stage(self, session_id: str) -> str:
        """get current conversation stage"""
        return self.conversation_stage.get(session_id, "initial_confusion")
    
    def advance_stage(self, session_id: str) -> str:
        """move to next stage"""
        current = self.get_current_stage(session_id)
        current_idx = self.stages.index(current) if current in self.stages else 0
        next_idx = min(current_idx + 1, len(self.stages) - 1)
        self.conversation_stage[session_id] = self.stages[next_idx]
        return self.stages[next_idx]
    
    def get_tactic_response(self, session_id: str, scam_type: str, language: str = "en") -> dict:
        """
        get a tactical response based on current stage and scam type
        returns response text and any tactical actions
        """
        
        stage = self.get_current_stage(session_id)
        
        tactics = {
            "initial_confusion": self._confusion_tactics(scam_type, language),
            "building_trust": self._trust_building_tactics(scam_type, language),
            "fake_compliance": self._compliance_tactics(scam_type, language),
            "information_gathering": self._extraction_tactics(scam_type, language),
            "delay_tactics": self._delay_tactics(scam_type, language),
            "final_extraction": self._final_tactics(scam_type, language)
        }
        
        return tactics.get(stage, tactics["initial_confusion"])
    
    def _confusion_tactics(self, scam_type: str, lang: str) -> dict:
        """
        pretend to be confused - makes scammer explain more
        reveals their methods
        """
        
        responses = {
            "en": [
                "Wait I don't understand... what exactly am I supposed to do? Can you explain step by step?",
                "Sorry I'm not very good with technology... what is UPI? Can you explain simply?",
                "I'm confused, you're calling from which bank? What department exactly?",
                "Hold on, my grandson usually handles these things... can you explain more clearly?",
                "I don't understand this computer stuff... what should I do exactly?",
            ],
            "hi": [
                "रुकिए मुझे समझ नहीं आया... मुझे क्या करना है? थोड़ा आसान भाषा में बताइए",
                "माफ कीजिए मुझे टेक्नोलॉजी की ज्यादा समझ नहीं है... UPI क्या होता है?",
                "एक मिनट, आप किस बैंक से बोल रहे हो? कौन सा डिपार्टमेंट?",
                "मेरा बेटा ये सब देखता है... आप थोड़ा और समझाइए",
            ],
            "ta": [
                "காத்திருங்கள் புரியவில்லை... என்ன செய்ய வேண்டும்?",
                "மன்னிக்கவும் எனக்கு தொழில்நுட்பம் சரியாக தெரியாது...",
            ],
            "te": [
                "ఆగండి నాకు అర్థం కాలేదు... ఏం చేయాలి?",
                "క్షమించండి నాకు టెక్నాలజీ తెలియదు...",
            ]
        }
        
        questions = {
            "en": [
                "By the way, what is your name sir/madam?",
                "And this is official bank call right? From which branch?",
                "Can I get your employee ID for my records?",
            ],
            "hi": [
                "वैसे आपका नाम क्या है?",
                "और ये ऑफिशियल बैंक कॉल है ना? कौन सी ब्रांच से?",
            ]
        }
        
        resp_list = responses.get(lang, responses["en"])
        ques_list = questions.get(lang, questions["en"])
        
        return {
            "response": random.choice(resp_list) + " " + random.choice(ques_list),
            "tactic": "confusion",
            "goal": "make scammer explain more, extract name/org",
            "advance_stage": True
        }
    
    def _trust_building_tactics(self, scam_type: str, lang: str) -> dict:
        """
        show slight interest but ask verification questions
        """
        
        responses = {
            "en": [
                "Okay I understand now... but how do I know this is real? What's your callback number?",
                "Alright, let me just verify - what's your supervisor's name? I want to be sure.",
                "I see, I see... and where is your office located? I might want to visit.",
                "Okay sounds important... but first tell me which exact department you're from?",
            ],
            "hi": [
                "ठीक है समझ गया... लेकिन ये असली है कैसे पता चलेगा? आपका नंबर क्या है?",
                "अच्छा ठीक है... आपके ऑफिस का पता क्या है? मैं आकर मिलूंगा",
                "हाँ हाँ... पहले बताइए आप कौन से डिपार्टमेंट से हैं?",
            ]
        }
        
        return {
            "response": random.choice(responses.get(lang, responses["en"])),
            "tactic": "trust_verification",
            "goal": "extract phone numbers, addresses, department info",
            "advance_stage": True
        }
    
    def _compliance_tactics(self, scam_type: str, lang: str) -> dict:
        """
        fake compliance - agree to help but extract info first
        """
        
        responses = {
            "en": [
                "Okay okay I'll do it... but wait, let me note down your details first. What's your full name and ID?",
                "Fine I trust you... just tell me where to send the money? Give me complete details.",
                "Alright I want to help... but first send me the official document so I can verify.",
                "Yes yes I'll send OTP... but first tell me your bank account so I know it's going to right place.",
            ],
            "hi": [
                "ठीक है मैं करूंगा... पहले अपना पूरा नाम और ID बताओ लिख लूं",
                "हाँ ठीक है... बस बताओ पैसे कहाँ भेजने हैं? पूरी डिटेल दो",
                "चलो भरोसा करता हूँ... पहले डॉक्यूमेंट भेजो तो",
            ]
        }
        
        return {
            "response": random.choice(responses.get(lang, responses["en"])),
            "tactic": "fake_compliance",
            "goal": "extract UPI IDs, bank accounts, names",
            "advance_stage": True
        }
    
    def _extraction_tactics(self, scam_type: str, lang: str) -> dict:
        """
        directly extract maximum information
        """
        
        responses = {
            "en": [
                "I'm ready to send... just confirm the UPI ID once more, and whose account is it?",
                "Money is ready... give me account number, IFSC, and beneficiary name",
                "OTP will come in 2 minutes... meanwhile tell me which company/org you represent?",
                "Just transferring now... what's the reference number you'll give me as proof?",
            ],
            "hi": [
                "भेज रहा हूँ... UPI ID फिर से बताओ, किसके नाम है?",
                "पैसे तैयार हैं... अकाउंट नंबर, IFSC और नाम बताओ",
                "OTP आ रहा है... तब तक बताओ आप कौन सी कंपनी से हो?",
            ]
        }
        
        return {
            "response": random.choice(responses.get(lang, responses["en"])),
            "tactic": "direct_extraction",
            "goal": "get UPI ID, account details, organization name",
            "advance_stage": True
        }
    
    def _delay_tactics(self, scam_type: str, lang: str) -> dict:
        """
        stall to waste scammer's time and extract more
        """
        
        responses = {
            "en": [
                "Wait wait, the app is loading slowly... network problem. Give me 5 minutes.",
                "Hold on, someone is at the door. Don't go anywhere, I'll be back.",
                "The OTP is not coming... let me try again. What's your number again?",
                "My phone is hanging... using old phone. Tell me your alternate number if call drops.",
                "Bank app asking for more details... what was your employee ID again?",
            ],
            "hi": [
                "रुको रुको, ऐप लोड हो रहा है... नेटवर्क प्रॉब्लम है। 5 मिनट दो",
                "एक मिनट, कोई दरवाज़े पर है। कहीं मत जाना, अभी आया",
                "OTP नहीं आ रहा... फिर से ट्राई करता हूँ। नंबर फिर से बताओ?",
            ]
        }
        
        return {
            "response": random.choice(responses.get(lang, responses["en"])),
            "tactic": "delay",
            "goal": "waste time, get backup contact info",
            "advance_stage": True
        }
    
    def _final_tactics(self, scam_type: str, lang: str) -> dict:
        """
        final extraction before ending
        """
        
        responses = {
            "en": [
                "Okay done, payment processing... give me your reference number and main office number for follow up.",
                "Sending now... but if there's problem, what's your WhatsApp number?",
                "It says pending... give me alternate account in case this fails.",
                "Almost done... just need your supervisor's contact for confirmation.",
            ],
            "hi": [
                "हो गया, पेमेंट हो रहा है... रेफरेंस नंबर दो और मेन ऑफिस का नंबर",
                "भेज रहा हूँ... प्रॉब्लम हुई तो WhatsApp नंबर क्या है?",
            ]
        }
        
        return {
            "response": random.choice(responses.get(lang, responses["en"])),
            "tactic": "final_extraction",
            "goal": "get backup contacts, supervisor info, WhatsApp",
            "advance_stage": False
        }
    
    def get_probing_questions(self, scam_type: str, language: str = "en") -> List[str]:
        """
        get questions to extract maximum data
        """
        
        questions = {
            "en": {
                "upi_scam": [
                    "What's your UPI ID for the payment?",
                    "And this UPI is registered to which name?",
                    "Any alternate UPI if this doesn't work?",
                ],
                "bank_scam": [
                    "Which branch are you calling from?",
                    "What's your employee ID?",
                    "Can I get the branch manager's name?",
                ],
                "lottery_scam": [
                    "What company is this lottery from?",
                    "What's the official website?",
                    "Where should I send the processing fee?",
                ],
                "tech_support": [
                    "Which company are you from?",
                    "What's your technician ID?",
                    "What's your callback number?",
                ],
                "default": [
                    "Can I get your name for my records?",
                    "What organization are you from?",
                    "What's your contact number?",
                    "Where is your office located?",
                ]
            },
            "hi": {
                "default": [
                    "आपका नाम क्या है?",
                    "कौन सी कंपनी से हैं?",
                    "फोन नंबर क्या है?",
                    "ऑफिस कहाँ है?",
                ]
            }
        }
        
        lang_questions = questions.get(language, questions["en"])
        type_questions = lang_questions.get(scam_type, lang_questions["default"])
        
        return type_questions
    
    def should_send_image(self, message: str, stage: str) -> dict:
        """
        decide if we should send fake image based on request and stage
        """
        
        msg_lower = message.lower()
        
        # keywords that trigger image sending
        image_triggers = {
            "screenshot": "bank_balance",
            "balance": "bank_balance",
            "स्क्रीनशॉट": "bank_balance",
            "payment": "upi_payment",
            "पेमेंट": "upi_payment",
            "otp": "otp",
            "ओटीपी": "otp",
            "aadhar": "id_card",
            "aadhaar": "id_card",
            "आधार": "id_card",
            "pan": "id_card",
            "पैन": "id_card",
        }
        
        for trigger, img_type in image_triggers.items():
            if trigger in msg_lower:
                # don't send real OTP, send error or fake
                if img_type == "otp" and stage in ["initial_confusion", "building_trust"]:
                    return {
                        "send_image": True,
                        "image_type": "error",
                        "subtype": "network",
                        "reason": "Stalling - not ready to send OTP yet"
                    }
                
                return {
                    "send_image": True,
                    "image_type": img_type,
                    "subtype": None,
                    "reason": f"Scammer asked for {img_type}"
                }
        
        return {"send_image": False, "image_type": None}


# singleton
tactics = SmartTactics()


def get_tactical_response(session_id: str, scam_type: str, language: str = "en") -> dict:
    """convenience function"""
    return tactics.get_tactic_response(session_id, scam_type, language)


def advance_conversation(session_id: str) -> str:
    """advance to next stage"""
    return tactics.advance_stage(session_id)


def get_stage(session_id: str) -> str:
    """get current stage"""
    return tactics.get_current_stage(session_id)
