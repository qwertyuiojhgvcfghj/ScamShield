"""
scam_detector.py

detects scam intent from messages using keyword matching & patterns.
supports multiple indian languages.
not perfect but works well for common indian scams (bank, upi, kyc etc)
"""

import re

# common scam keywords - collected from real scam messages
# grouped by category for easier maintenance
SCAM_KEYWORDS = {
    "urgency": [
        "urgent", "immediately", "right now", "asap", "hurry",
        "within 24 hours", "last chance", "final warning", "act now",
        "don't delay", "expire today", "suspended", "blocked",
        # Hindi
        "तुरंत", "जल्दी", "अभी", "ब्लॉक", "सस्पेंड", "बंद हो जाएगा",
        # Tamil
        "உடனடியாக", "தடுக்கப்பட்டது", "நிறுத்தப்பட்டது",
        # Telugu
        "వెంటనే", "బ్లాక్", "సస్పెండ్"
    ],
    "banking": [
        "bank account", "account blocked", "account suspended", "verify account",
        "update kyc", "kyc expired", "pan card", "aadhar", "aadhaar",
        "credit card", "debit card", "atm pin", "cvv", "card number",
        "sbi", "hdfc", "icici", "axis", "rbi", "reserve bank",
        # Hindi
        "बैंक खाता", "खाता बंद", "केवाईसी", "पैन कार्ड", "आधार",
        # Tamil
        "வங்கி கணக்கு", "கணக்கு தடுக்கப்பட்டது",
        # Telugu
        "బ్యాంక్ ఖాతా", "ఖాతా బ్లాక్"
    ],
    "upi": [
        "upi", "upi id", "upi pin", "paytm", "phonepe", "gpay", "google pay",
        "bhim", "@ybl", "@paytm", "@oksbi", "@okicici", "@okaxis",
        "send money", "transfer money", "payment failed",
        # Hindi
        "यूपीआई", "पेटीएम", "फोनपे", "पैसे भेजो", "ट्रांसफर",
        # Tamil
        "பணம் அனுப்பு", "பேமென்ட்"
    ],
    "otp_password": [
        "otp", "one time password", "password", "pin", "secret code",
        "verification code", "security code", "cvv", "mpin",
        # Hindi
        "ओटीपी", "पासवर्ड", "पिन", "गुप्त कोड",
        # Tamil
        "கடவுச்சொல்", "ஓடிபி",
        # Telugu
        "ఓటీపీ", "పాస్వర్డ్"
    ],
    "lottery_prize": [
        "congratulations", "you won", "winner", "lottery", "prize",
        "lucky draw", "scratch card", "gift card", "free gift",
        "claim now", "reward", "cashback", "bonus",
        # Hindi
        "बधाई हो", "जीत गए", "लॉटरी", "इनाम", "गिफ्ट",
        # Tamil
        "வாழ்த்துக்கள்", "வென்றீர்கள்", "பரிசு"
    ],
    "threats": [
        "legal action", "police", "arrest", "fir", "court", "jail",
        "case filed", "cyber crime", "investigation", "fraud department",
        # Hindi
        "कानूनी कार्रवाई", "पुलिस", "गिरफ्तार", "कोर्ट", "जेल", "एफआईआर",
        # Tamil
        "சட்ட நடவடிக்கை", "போலீஸ்", "கைது"
    ],
    "links_requests": [
        "click here", "click link", "click below", "visit link",
        "download app", "install app", "fill form", "update details",
        # Hindi
        "क्लिक करें", "लिंक पर जाएं", "ऐप डाउनलोड करें",
        # Tamil
        "கிளிக் செய்யவும்", "லிங்க்"
    ]
}

# flatten for quick lookup
ALL_KEYWORDS = []
for category, words in SCAM_KEYWORDS.items():
    ALL_KEYWORDS.extend(words)

# suspicious patterns (regex)
SUSPICIOUS_PATTERNS = [
    r"http[s]?://(?!.*(?:gov\.in|sbi\.co\.in|hdfcbank\.com|icicibank\.com))[^\s]+",  # non-bank links
    r"\b\d{10}\b",  # 10 digit numbers (phone)
    r"\+91[\s-]?\d{10}",  # indian phone format
    r"[a-zA-Z0-9._-]+@[a-z]{2,10}",  # upi id pattern
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # card numbers
    r"rs\.?\s*\d+",  # money amounts
    r"₹\s*\d+",  # rupee symbol
]


def detect_scam(text):
    """
    checks if message looks like a scam
    
    returns dict with:
        - is_scam: bool
        - confidence: float (0-1)
        - matched_keywords: list
        - categories: list of scam types detected
    """
    if not text:
        return {"is_scam": False, "confidence": 0, "matched_keywords": [], "categories": []}
    
    text_lower = text.lower()
    
    matched_keywords = []
    matched_categories = set()
    
    # check keywords
    for category, keywords in SCAM_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                matched_keywords.append(kw)
                matched_categories.add(category)
    
    # check patterns
    pattern_matches = 0
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            pattern_matches += 1
    
    # calculate confidence score
    # more keywords + patterns = higher confidence
    keyword_score = min(len(matched_keywords) / 5, 1.0)  # cap at 1
    pattern_score = min(pattern_matches / 3, 1.0)
    category_score = min(len(matched_categories) / 3, 1.0)
    
    # weighted average
    confidence = (keyword_score * 0.4) + (pattern_score * 0.3) + (category_score * 0.3)
    
    # bump confidence if multiple categories detected (more suspicious)
    if len(matched_categories) >= 2:
        confidence = min(confidence + 0.15, 1.0)
    
    # its a scam if confidence > 0.3 (tuned through testing)
    is_scam = confidence >= 0.3
    
    return {
        "is_scam": is_scam,
        "confidence": round(confidence, 2),
        "matched_keywords": list(set(matched_keywords)),  # dedupe
        "categories": list(matched_categories)
    }


def analyze_conversation(messages):
    """
    analyze entire conversation history for scam patterns
    useful for borderline cases where single msg might not be enough
    """
    if not messages:
        return {"is_scam": False, "confidence": 0, "matched_keywords": [], "categories": []}
    
    # combine all scammer messages
    scammer_texts = [msg["text"] for msg in messages if msg.get("sender") == "scammer"]
    combined = " ".join(scammer_texts)
    
    return detect_scam(combined)


# quick test
if __name__ == "__main__":
    test_msgs = [
        "Your SBI account is blocked! Call now to verify KYC.",
        "Hey, what's up?",
        "Congratulations! You won Rs.50000 in lucky draw. Click link to claim.",
        "UPI transaction failed. Share OTP to verify.",
        "Let's meet for coffee tomorrow",
    ]
    
    for msg in test_msgs:
        result = detect_scam(msg)
        print(f"\n'{msg[:50]}...'")
        print(f"  Scam: {result['is_scam']} | Confidence: {result['confidence']}")
        print(f"  Keywords: {result['matched_keywords'][:3]}")
