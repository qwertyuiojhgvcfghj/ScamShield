"""
scam_classifier.py

classifies scam types to use type-specific engagement tactics.
uses keyword matching - no API needed.

scam types:
- BANKING: fake bank calls, account blocked
- LOTTERY: prize winning, lucky draw
- TECH_SUPPORT: computer virus, remote access
- KYC: aadhar/pan linking, kyc update
- JOB: fake job offers, work from home
- LOAN: instant loan, pre-approved
- INVESTMENT: crypto, stock tips, doubling money
- ROMANCE: dating scams, emotional manipulation
- DELIVERY: fake courier, customs fees
- GOVERNMENT: fake police, tax dept, legal threats
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ScamClassification:
    """result of scam classification"""
    scam_type: str
    confidence: float  # 0.0 to 1.0
    matched_keywords: List[str]
    suggested_tactics: List[str]


# scam type keywords
SCAM_PATTERNS = {
    "BANKING": {
        "keywords": [
            "bank", "account", "blocked", "suspended", "debit card", "credit card",
            "atm", "pin", "cvv", "otp", "net banking", "mobile banking", "upi",
            "transaction", "transfer", "ifsc", "branch", "manager", "rbi",
            "बैंक", "खाता", "ब्लॉक", "एटीएम", "ट्रांसफर"
        ],
        "tactics": [
            "Ask which bank and branch",
            "Ask for employee ID",
            "Pretend confusion about account number",
            "Ask them to verify YOUR details first"
        ]
    },
    "LOTTERY": {
        "keywords": [
            "lottery", "winner", "won", "prize", "jackpot", "lucky draw",
            "congratulations", "million", "lakh", "crore", "claim", "lucky",
            "selected", "random", "jio", "amazon", "flipkart",
            "लॉटरी", "जीत", "इनाम", "लकी"
        ],
        "tactics": [
            "Act excited but confused",
            "Ask how you entered the lottery",
            "Ask for official website",
            "Request physical letter/certificate"
        ]
    },
    "TECH_SUPPORT": {
        "keywords": [
            "virus", "malware", "hacked", "computer", "laptop", "microsoft",
            "windows", "apple", "support", "technician", "remote", "anydesk",
            "teamviewer", "download", "install", "software", "security",
            "कंप्यूटर", "वायरस", "हैक"
        ],
        "tactics": [
            "Pretend to be tech-illiterate",
            "Ask them to explain slowly",
            "Say you need grandson's help",
            "Keep asking 'which button?'"
        ]
    },
    "KYC": {
        "keywords": [
            "kyc", "aadhar", "aadhaar", "pan", "pan card", "link", "update",
            "verify", "verification", "expir", "document", "upload", "sebi",
            "mutual fund", "demat",
            "आधार", "पैन", "केवाईसी", "अपडेट"
        ],
        "tactics": [
            "Ask why bank didn't inform",
            "Say you'll visit branch",
            "Ask for reference number",
            "Pretend aadhar is with family member"
        ]
    },
    "JOB": {
        "keywords": [
            "job", "vacancy", "hiring", "work from home", "wfh", "salary",
            "income", "earning", "part time", "full time", "offer letter",
            "interview", "hr", "recruitment", "typing job", "data entry",
            "नौकरी", "जॉब", "सैलरी", "वर्क फ्रॉम होम"
        ],
        "tactics": [
            "Ask about company registration",
            "Ask for office address to visit",
            "Request official email from company domain",
            "Ask about PF/ESI benefits"
        ]
    },
    "LOAN": {
        "keywords": [
            "loan", "pre-approved", "instant loan", "personal loan",
            "home loan", "emi", "interest", "processing fee", "sanction",
            "credit score", "cibil", "disburs",
            "लोन", "ऋण", "ब्याज", "किश्त"
        ],
        "tactics": [
            "Ask why processing fee before disbursement",
            "Ask for RBI license number",
            "Say you'll check with bank first",
            "Request physical documents"
        ]
    },
    "INVESTMENT": {
        "keywords": [
            "invest", "trading", "stock", "share", "crypto", "bitcoin",
            "forex", "profit", "return", "double", "guaranteed", "scheme",
            "portfolio", "broker", "tip",
            "निवेश", "शेयर", "मुनाफा", "रिटर्न"
        ],
        "tactics": [
            "Ask for SEBI registration",
            "Ask how they got your number",
            "Say you need to consult CA first",
            "Ask for past verified returns proof"
        ]
    },
    "ROMANCE": {
        "keywords": [
            "dear", "darling", "love", "relationship", "marry", "lonely",
            "beautiful", "handsome", "gift", "parcel", "customs", "stuck",
            "army", "soldier", "abroad", "foreign",
        ],
        "tactics": [
            "Ask for video call",
            "Ask why they chose you",
            "Ask for family members contact",
            "Request meeting in person"
        ]
    },
    "DELIVERY": {
        "keywords": [
            "courier", "parcel", "delivery", "customs", "stuck", "warehouse",
            "dhl", "fedex", "bluedart", "fees", "clearance", "import",
            "पार्सल", "कूरियर", "डिलीवरी"
        ],
        "tactics": [
            "Ask for tracking number",
            "Say you didn't order anything",
            "Ask for sender details",
            "Request official customs document"
        ]
    },
    "GOVERNMENT": {
        "keywords": [
            "police", "cyber cell", "legal", "court", "arrest", "warrant",
            "summon", "income tax", "gst", "enforcement", "narcotics",
            "crime", "case", "fir", "complaint",
            "पुलिस", "कोर्ट", "गिरफ्तार", "कानूनी"
        ],
        "tactics": [
            "Act scared and confused",
            "Ask for badge number/ID",
            "Say you'll come to station",
            "Ask for official letter/email"
        ]
    }
}


def classify_scam(text: str, conversation: List[str] = None) -> ScamClassification:
    """
    classify the type of scam based on text.
    
    args:
        text: current message
        conversation: optional list of all messages for context
    
    returns:
        ScamClassification with type, confidence, and tactics
    """
    
    # combine current and conversation for analysis
    full_text = text.lower()
    if conversation:
        full_text = " ".join([m.lower() for m in conversation]) + " " + full_text
    
    # score each scam type
    scores: Dict[str, Tuple[float, List[str]]] = {}
    
    for scam_type, data in SCAM_PATTERNS.items():
        keywords = data["keywords"]
        matched = []
        
        for kw in keywords:
            if kw.lower() in full_text:
                matched.append(kw)
        
        if matched:
            # confidence based on unique keyword matches
            confidence = min(len(matched) / 3, 1.0)  # 3+ keywords = 100%
            scores[scam_type] = (confidence, matched)
    
    if not scores:
        return ScamClassification(
            scam_type="UNKNOWN",
            confidence=0.0,
            matched_keywords=[],
            suggested_tactics=["Stay vague", "Ask clarifying questions", "Act confused"]
        )
    
    # get highest scoring type
    best_type = max(scores, key=lambda x: scores[x][0])
    confidence, matched = scores[best_type]
    tactics = SCAM_PATTERNS[best_type]["tactics"]
    
    return ScamClassification(
        scam_type=best_type,
        confidence=confidence,
        matched_keywords=matched,
        suggested_tactics=tactics
    )


def get_scam_type(text: str) -> str:
    """simple function to get scam type string"""
    return classify_scam(text).scam_type


def get_tactics_for_scam(scam_type: str) -> List[str]:
    """get suggested tactics for a scam type"""
    if scam_type in SCAM_PATTERNS:
        return SCAM_PATTERNS[scam_type]["tactics"]
    return ["Stay vague", "Ask clarifying questions"]


# test
if __name__ == "__main__":
    test_messages = [
        "Your SBI account has been blocked! Share OTP immediately.",
        "Congratulations! You won Rs 50 lakh in Jio lottery!",
        "Your computer has virus. Download Anydesk for support.",
        "Your KYC is expiring. Link Aadhar to avoid deactivation.",
        "Earn Rs 50,000 per month work from home typing job!",
        "You are under investigation by cyber crime police.",
    ]
    
    print("Testing scam classifier...\n")
    
    for msg in test_messages:
        result = classify_scam(msg)
        print(f"Message: {msg[:50]}...")
        print(f"  Type: {result.scam_type} ({result.confidence:.0%})")
        print(f"  Matched: {result.matched_keywords[:3]}")
        print(f"  Tactic: {result.suggested_tactics[0]}")
        print()
