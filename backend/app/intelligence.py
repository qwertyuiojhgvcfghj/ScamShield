"""
intelligence.py - ENHANCED VERSION

extracts MAXIMUM actionable intel from scam conversations.
uses ONLY regex and code - NO API NEEDED!

extracts:
- UPI IDs (all providers)
- Phone numbers (Indian + international)
- Bank account numbers
- IFSC codes
- URLs/links
- Email addresses
- Cryptocurrency addresses (BTC, ETH)
- Card numbers
- Aadhar numbers (partial)
- PAN numbers
- Names (heuristic)
- Amounts/money references
- Keywords & tactics

author: honeypot team
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Set
from datetime import datetime


@dataclass
class ExtractedIntel:
    """holds all extracted intelligence from a conversation"""
    
    # core financial
    bank_accounts: List[str] = field(default_factory=list)
    upi_ids: List[str] = field(default_factory=list)
    ifsc_codes: List[str] = field(default_factory=list)
    card_numbers: List[str] = field(default_factory=list)
    
    # contact info
    phone_numbers: List[str] = field(default_factory=list)
    email_addresses: List[str] = field(default_factory=list)
    whatsapp_numbers: List[str] = field(default_factory=list)
    
    # web/links
    phishing_links: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    
    # identity
    aadhar_numbers: List[str] = field(default_factory=list)
    pan_numbers: List[str] = field(default_factory=list)
    names: List[str] = field(default_factory=list)
    
    # crypto
    crypto_addresses: List[str] = field(default_factory=list)
    
    # financial amounts
    amounts: List[str] = field(default_factory=list)
    
    # analysis
    suspicious_keywords: List[str] = field(default_factory=list)
    tactics_detected: List[str] = field(default_factory=list)
    scam_type: str = ""
    risk_score: int = 0
    
    def to_dict(self) -> Dict:
        """convert to dict for json response - deduped"""
        return {
            "bankAccounts": list(set(self.bank_accounts)),
            "upiIds": list(set(self.upi_ids)),
            "ifscCodes": list(set(self.ifsc_codes)),
            "cardNumbers": list(set(self.card_numbers)),
            "phoneNumbers": list(set(self.phone_numbers)),
            "emailAddresses": list(set(self.email_addresses)),
            "whatsappNumbers": list(set(self.whatsapp_numbers)),
            "phishingLinks": list(set(self.phishing_links)),
            "domains": list(set(self.domains)),
            "aadharNumbers": list(set(self.aadhar_numbers)),
            "panNumbers": list(set(self.pan_numbers)),
            "names": list(set(self.names)),
            "cryptoAddresses": list(set(self.crypto_addresses)),
            "amounts": list(set(self.amounts)),
            "suspiciousKeywords": list(set(self.suspicious_keywords)),
            "tacticsDetected": list(set(self.tactics_detected)),
            "scamType": self.scam_type,
            "riskScore": self.risk_score
        }
    
    def merge(self, other: 'ExtractedIntel'):
        """combine intel from another extraction"""
        self.bank_accounts.extend(other.bank_accounts)
        self.upi_ids.extend(other.upi_ids)
        self.ifsc_codes.extend(other.ifsc_codes)
        self.card_numbers.extend(other.card_numbers)
        self.phone_numbers.extend(other.phone_numbers)
        self.email_addresses.extend(other.email_addresses)
        self.whatsapp_numbers.extend(other.whatsapp_numbers)
        self.phishing_links.extend(other.phishing_links)
        self.domains.extend(other.domains)
        self.aadhar_numbers.extend(other.aadhar_numbers)
        self.pan_numbers.extend(other.pan_numbers)
        self.names.extend(other.names)
        self.crypto_addresses.extend(other.crypto_addresses)
        self.amounts.extend(other.amounts)
        self.suspicious_keywords.extend(other.suspicious_keywords)
        self.tactics_detected.extend(other.tactics_detected)
        
        # keep highest risk score
        self.risk_score = max(self.risk_score, other.risk_score)
        
        # keep scam type if we don't have one
        if not self.scam_type and other.scam_type:
            self.scam_type = other.scam_type
    
    def is_empty(self) -> bool:
        return not any([
            self.bank_accounts, self.upi_ids, self.phishing_links,
            self.phone_numbers, self.email_addresses, self.suspicious_keywords,
            self.aadhar_numbers, self.pan_numbers, self.crypto_addresses
        ])
    
    def get_intel_count(self) -> int:
        """count total intel pieces"""
        return (
            len(set(self.bank_accounts)) +
            len(set(self.upi_ids)) +
            len(set(self.phone_numbers)) +
            len(set(self.email_addresses)) +
            len(set(self.phishing_links)) +
            len(set(self.names))
        )


# =============================================================
# COMPREHENSIVE REGEX PATTERNS
# =============================================================

PATTERNS = {
    # UPI IDs - all major providers in India
    "upi_id": [
        # standard format: user@provider
        r"[a-zA-Z0-9._-]+@(?:ybl|paytm|oksbi|okaxis|okicici|okhdfcbank|okhdfc|upi|axl|ibl|sbi|apl|ratn|icici|hdfcbank|axisbank|kotak|indus|federal|pnb|boi|bob|cbi|iob|canara|uco|syndicate|allahabad|vijaya|dena|andhra|corporation|indian|united|idbi|bandhan|rbl|yes|nsdl|airtel|jio|freecharge|mobikwik|phonepe|gpay|amazonpay|slice|cred|groww|bajaj|jupiter|fi|navi|payzapp|hsbc|citi|sc|dbs|rbs|barclays)\b",
        # number@provider
        r"\b\d{10}@(?:ybl|paytm|oksbi|okaxis|okicici|upi|sbi|axl|ibl|phonepe|gpay)\b",
    ],
    
    # Phone numbers - comprehensive Indian formats
    "phone": [
        r"\+91[\s.-]?\d{5}[\s.-]?\d{5}",           # +91 XXXXX XXXXX
        r"\+91[\s.-]?\d{10}",                       # +91 XXXXXXXXXX
        r"91[\s.-]?\d{10}\b",                       # 91XXXXXXXXXX
        r"\b0\d{2,4}[\s.-]?\d{6,8}\b",              # landline: 0XX-XXXXXXXX
        r"\b[6-9]\d{9}\b",                          # mobile: 9XXXXXXXXX
        r"\b[6-9]\d{4}[\s.-]?\d{5}\b",              # mobile with space
        r"(?:call|contact|whatsapp|ph|phone|mobile|mob|cell|tel)[\s:]*[+]?[\d\s.-]{10,15}",
    ],
    
    # Bank account numbers
    "bank_account": [
        r"\b\d{9,18}\b",                            # 9-18 digits
        r"\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{2,6}\b",  # formatted
        r"(?:a/c|ac|account|acct)[\s.:#]*\d{9,18}",  # with prefix
    ],
    
    # IFSC codes - Indian bank codes
    "ifsc": [
        r"\b[A-Z]{4}0[A-Z0-9]{6}\b",                # standard IFSC
        r"(?:ifsc|ifsc code)[\s:]*[A-Z]{4}0[A-Z0-9]{6}",
    ],
    
    # Card numbers
    "card": [
        r"\b4\d{3}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",   # Visa
        r"\b5[1-5]\d{2}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",  # Mastercard
        r"\b3[47]\d{2}[\s.-]?\d{6}[\s.-]?\d{5}\b",   # Amex
        r"\b6(?:011|5\d{2})[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",  # Discover
        r"\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",  # generic 16 digit
    ],
    
    # Email addresses
    "email": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        r"(?:email|mail|e-mail)[\s:]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",
    ],
    
    # URLs and links
    "link": [
        r"https?://[^\s<>\"'\]\)]+",
        r"www\.[^\s<>\"'\]\)]+",
        r"\b[a-z0-9][-a-z0-9]*\.[a-z]{2,}(?:/[^\s]*)?",  # domain.tld/path
    ],
    
    # Aadhar numbers (12 digits)
    "aadhar": [
        r"\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",
        r"(?:aadhar|aadhaar|uid)[\s:#]*\d{4}[\s.-]?\d{4}[\s.-]?\d{4}",
    ],
    
    # PAN numbers
    "pan": [
        r"\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b",
        r"(?:pan|pan card|pan no)[\s:#]*[A-Z]{5}\d{4}[A-Z]",
    ],
    
    # Cryptocurrency addresses
    "crypto": [
        r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",     # Bitcoin
        r"\bbc1[a-zA-HJ-NP-Z0-9]{39,59}\b",         # Bitcoin bech32
        r"\b0x[a-fA-F0-9]{40}\b",                    # Ethereum
        r"\bT[A-Za-z1-9]{33}\b",                     # Tron
        r"\b[LM][a-km-zA-HJ-NP-Z1-9]{26,33}\b",     # Litecoin
    ],
    
    # Money amounts (Indian Rupees)
    "amount": [
        r"₹[\s]?[\d,]+(?:\.\d{1,2})?",              # ₹ symbol
        r"Rs\.?[\s]?[\d,]+(?:\.\d{1,2})?",          # Rs. prefix
        r"INR[\s]?[\d,]+(?:\.\d{1,2})?",            # INR prefix
        r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:rupees?|rs|inr|lakhs?|crores?|k)\b",
        r"(?:amount|payment|send|transfer|pay)[\s:]*(?:₹|Rs\.?|INR)?[\s]?[\d,]+",
    ],
    
    # WhatsApp specific
    "whatsapp": [
        r"(?:whatsapp|wa|watsapp|whats app)[\s:]*[+]?\d[\d\s.-]{9,15}",
        r"wa\.me/\d+",
    ],
}

# Suspicious keywords by category
KEYWORD_CATEGORIES = {
    "urgency": [
        "urgent", "immediately", "now", "quick", "fast", "hurry",
        "deadline", "expire", "expiring", "last chance", "limited time",
        "तुरंत", "जल्दी", "अभी", "फटाफट"
    ],
    "threat": [
        "blocked", "suspended", "closed", "terminated", "deactivate",
        "arrest", "legal", "police", "court", "fir", "case", "jail",
        "action", "penalty", "fine", "seize", "freeze",
        "ब्लॉक", "बंद", "गिरफ्तार", "पुलिस", "कोर्ट"
    ],
    "credential": [
        "otp", "pin", "password", "cvv", "expiry", "mpin",
        "verify", "verification", "authenticate", "confirm",
        "ओटीपी", "पिन", "पासवर्ड"
    ],
    "financial": [
        "transfer", "payment", "pay", "send", "receive", "refund",
        "cashback", "bonus", "credit", "debit", "deposit", "withdraw",
        "पैसे", "भेजो", "ट्रांसफर", "रिफंड"
    ],
    "prize": [
        "won", "winner", "prize", "lottery", "lucky", "congratulations",
        "reward", "gift", "free", "selected", "chosen",
        "जीत", "इनाम", "लॉटरी", "बधाई"
    ],
    "identity": [
        "kyc", "aadhar", "aadhaar", "pan", "id proof", "document",
        "upload", "submit", "provide",
        "आधार", "पैन", "केवाईसी"
    ],
    "click_bait": [
        "click", "link", "website", "visit", "open", "download",
        "install", "update", "upgrade",
        "क्लिक", "लिंक", "खोलो"
    ]
}

# Known safe domains - don't flag as phishing
SAFE_DOMAINS = [
    "sbi.co.in", "onlinesbi.com", "onlinesbi.sbi", "sbiyono.sbi",
    "hdfcbank.com", "netbanking.hdfcbank.com",
    "icicibank.com", "infinity.icicibank.com",
    "axisbank.com", "omniconnect.axisbank.com",
    "kotak.com", "kotakmahindrabank.com",
    "yesbank.in", "pnbindia.in", "bankofindia.co.in",
    "bankofbaroda.in", "canarabank.com", "unionbankofindia.co.in",
    "rbi.org.in", "npci.org.in", "uidai.gov.in",
    "google.com", "gmail.com", "paytm.com", "phonepe.com",
    "googlepay.com", "amazon.in", "flipkart.com",
    "gov.in", "nic.in", "india.gov.in"
]

# Suspicious domain patterns
SUSPICIOUS_DOMAIN_PATTERNS = [
    r".*sbi.*verify.*", r".*bank.*secure.*", r".*kyc.*update.*",
    r".*account.*verify.*", r".*login.*bank.*", r".*otp.*verify.*",
    r"bit\.ly", r"tinyurl\.com", r"short\.link", r"t\.co",
    r".*\.xyz$", r".*\.tk$", r".*\.ml$", r".*\.ga$", r".*\.cf$",
    r".*-secure.*", r".*-verify.*", r".*-update.*"
]


def extract_upi_ids(text: str) -> List[str]:
    """extract all UPI IDs from text"""
    upi_ids = []
    for pattern in PATTERNS["upi_id"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        upi_ids.extend(matches)
    return list(set(upi_ids))


def extract_phone_numbers(text: str) -> List[str]:
    """extract all phone numbers from text"""
    phones = []
    for pattern in PATTERNS["phone"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            # clean and normalize
            clean = re.sub(r"[\s.-]", "", m)
            clean = re.sub(r"^(call|contact|whatsapp|ph|phone|mobile|mob|cell|tel):?", "", clean, flags=re.I)
            clean = clean.strip()
            if len(clean) >= 10 and clean.replace("+", "").isdigit():
                phones.append(clean)
    return list(set(phones))


def extract_bank_accounts(text: str) -> List[str]:
    """extract bank account numbers"""
    accounts = []
    for pattern in PATTERNS["bank_account"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            clean = re.sub(r"[\s.-]", "", m)
            clean = re.sub(r"^(a/c|ac|account|acct):?", "", clean, flags=re.I)
            # filter: 9-18 digits, not all same digit, not a phone number pattern
            if 9 <= len(clean) <= 18 and len(set(clean)) > 2:
                # additional check: shouldn't start with 6-9 and be exactly 10 digits (phone)
                if not (len(clean) == 10 and clean[0] in "6789"):
                    accounts.append(clean)
    return list(set(accounts))


def extract_ifsc_codes(text: str) -> List[str]:
    """extract IFSC codes"""
    ifsc = []
    for pattern in PATTERNS["ifsc"]:
        matches = re.findall(pattern, text.upper())
        ifsc.extend(matches)
    return list(set(ifsc))


def extract_card_numbers(text: str) -> List[str]:
    """extract credit/debit card numbers"""
    cards = []
    for pattern in PATTERNS["card"]:
        matches = re.findall(pattern, text)
        for m in matches:
            clean = re.sub(r"[\s.-]", "", m)
            # basic Luhn check could be added here
            if len(clean) in [15, 16]:
                # mask middle digits for safety
                masked = clean[:4] + "XXXX" + clean[-4:]
                cards.append(masked)
    return list(set(cards))


def extract_emails(text: str) -> List[str]:
    """extract email addresses"""
    emails = []
    for pattern in PATTERNS["email"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        emails.extend([e.lower() for e in matches if "@" in str(e)])
    return list(set(emails))


def extract_links(text: str) -> tuple:
    """extract URLs and domains, separating safe from suspicious"""
    links = []
    domains = []
    
    for pattern in PATTERNS["link"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for link in matches:
            # extract domain
            domain_match = re.search(r"(?:https?://)?(?:www\.)?([^/\s]+)", link)
            if domain_match:
                domain = domain_match.group(1).lower()
                
                # check if safe
                is_safe = any(safe in domain for safe in SAFE_DOMAINS)
                
                # check if suspicious pattern
                is_suspicious = any(re.match(pat, domain) for pat in SUSPICIOUS_DOMAIN_PATTERNS)
                
                if not is_safe or is_suspicious:
                    links.append(link)
                    domains.append(domain)
    
    return list(set(links)), list(set(domains))


def extract_aadhar(text: str) -> List[str]:
    """extract Aadhar numbers (masked)"""
    aadhar = []
    for pattern in PATTERNS["aadhar"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            clean = re.sub(r"[\s.-]", "", m)
            clean = re.sub(r"^(aadhar|aadhaar|uid):?", "", clean, flags=re.I)
            if len(clean) == 12 and clean.isdigit():
                # mask for privacy: show only last 4
                masked = "XXXX-XXXX-" + clean[-4:]
                aadhar.append(masked)
    return list(set(aadhar))


def extract_pan(text: str) -> List[str]:
    """extract PAN numbers"""
    pan = []
    for pattern in PATTERNS["pan"]:
        matches = re.findall(pattern, text.upper())
        pan.extend(matches)
    return list(set(pan))


def extract_crypto(text: str) -> List[str]:
    """extract cryptocurrency addresses"""
    crypto = []
    for pattern in PATTERNS["crypto"]:
        matches = re.findall(pattern, text)
        crypto.extend(matches)
    return list(set(crypto))


def extract_amounts(text: str) -> List[str]:
    """extract money amounts"""
    amounts = []
    for pattern in PATTERNS["amount"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend([m.strip() for m in matches])
    return list(set(amounts))


def extract_whatsapp(text: str) -> List[str]:
    """extract WhatsApp numbers"""
    wa = []
    for pattern in PATTERNS["whatsapp"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            clean = re.sub(r"[\s.-]", "", m)
            clean = re.sub(r"^(whatsapp|wa|watsapp|whatsapp):?", "", clean, flags=re.I)
            if clean:
                wa.append(clean)
    return list(set(wa))


def extract_names(text: str) -> List[str]:
    """
    extract potential names using heuristics
    looks for patterns like "I am X", "name is X", "this is X calling"
    """
    names = []
    
    name_patterns = [
        r"(?:my name is|i am|this is|myself|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:name|naam)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:mr\.|mrs\.|ms\.|shri|smt\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:from|calling from)\s+(?:bank|sbi|hdfc|icici)[\s,]+(?:my name is\s+)?([A-Z][a-z]+)",
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            name = m.strip()
            # filter out common false positives
            false_positives = ["Sir", "Madam", "Dear", "Customer", "Account", "Bank", "The", "This", "Your"]
            if name and name not in false_positives and len(name) > 2:
                names.append(name.title())
    
    return list(set(names))


def extract_keywords(text: str) -> tuple:
    """extract suspicious keywords and categorize them"""
    text_lower = text.lower()
    keywords = []
    categories = []
    
    for category, kw_list in KEYWORD_CATEGORIES.items():
        for kw in kw_list:
            if kw.lower() in text_lower:
                keywords.append(kw)
                if category not in categories:
                    categories.append(category)
    
    return list(set(keywords)), categories


def calculate_risk_score(intel: ExtractedIntel) -> int:
    """
    calculate risk score 0-100 based on extracted intel
    """
    score = 0
    
    # high value targets
    if intel.upi_ids: score += 25
    if intel.bank_accounts: score += 20
    if intel.card_numbers: score += 30
    if intel.aadhar_numbers: score += 15
    if intel.pan_numbers: score += 15
    
    # contact info
    if intel.phone_numbers: score += 10
    if intel.email_addresses: score += 5
    if intel.whatsapp_numbers: score += 10
    
    # links
    if intel.phishing_links: score += 20
    
    # tactics
    if "threat" in intel.tactics_detected: score += 15
    if "credential" in intel.tactics_detected: score += 20
    if "urgency" in intel.tactics_detected: score += 10
    
    return min(score, 100)


def determine_scam_type(tactics: List[str], keywords: List[str]) -> str:
    """determine the type of scam based on tactics and keywords"""
    
    keywords_lower = [k.lower() for k in keywords]
    
    if any(k in keywords_lower for k in ["kyc", "aadhar", "pan", "verify"]):
        return "KYC_SCAM"
    
    if any(k in keywords_lower for k in ["won", "lottery", "prize", "winner"]):
        return "LOTTERY_SCAM"
    
    if any(k in keywords_lower for k in ["blocked", "suspended", "closed", "freeze"]):
        return "ACCOUNT_FREEZE_SCAM"
    
    if any(k in keywords_lower for k in ["arrest", "police", "legal", "court"]):
        return "LEGAL_THREAT_SCAM"
    
    if any(k in keywords_lower for k in ["refund", "cashback", "bonus"]):
        return "REFUND_SCAM"
    
    if any(k in keywords_lower for k in ["otp", "pin", "password", "cvv"]):
        return "CREDENTIAL_PHISHING"
    
    if "click_bait" in tactics:
        return "PHISHING_LINK_SCAM"
    
    return "GENERAL_SCAM"


def extract_from_text(text: str) -> ExtractedIntel:
    """
    MAIN FUNCTION: extract all intel from a single message
    """
    intel = ExtractedIntel()
    
    if not text:
        return intel
    
    # extract everything
    intel.upi_ids = extract_upi_ids(text)
    intel.phone_numbers = extract_phone_numbers(text)
    intel.bank_accounts = extract_bank_accounts(text)
    intel.ifsc_codes = extract_ifsc_codes(text)
    intel.card_numbers = extract_card_numbers(text)
    intel.email_addresses = extract_emails(text)
    intel.phishing_links, intel.domains = extract_links(text)
    intel.aadhar_numbers = extract_aadhar(text)
    intel.pan_numbers = extract_pan(text)
    intel.crypto_addresses = extract_crypto(text)
    intel.amounts = extract_amounts(text)
    intel.whatsapp_numbers = extract_whatsapp(text)
    intel.names = extract_names(text)
    
    # keywords and tactics
    intel.suspicious_keywords, intel.tactics_detected = extract_keywords(text)
    
    # calculate risk and determine scam type
    intel.risk_score = calculate_risk_score(intel)
    intel.scam_type = determine_scam_type(intel.tactics_detected, intel.suspicious_keywords)
    
    return intel


def extract_from_conversation(messages: List[Dict]) -> ExtractedIntel:
    """
    extract intel from entire conversation history
    """
    combined = ExtractedIntel()
    
    for msg in messages:
        text = msg.get("text", "")
        intel = extract_from_text(text)
        combined.merge(intel)
    
    # recalculate after merging
    combined.risk_score = calculate_risk_score(combined)
    
    return combined


def generate_agent_notes(intel: ExtractedIntel, scam_result: Dict = None) -> str:
    """
    generate human-readable summary of scammer behavior
    """
    notes = []
    
    # scam type
    if intel.scam_type:
        notes.append(f"Scam Type: {intel.scam_type}")
    
    # risk level
    if intel.risk_score >= 70:
        notes.append(f"Risk Level: HIGH ({intel.risk_score}/100)")
    elif intel.risk_score >= 40:
        notes.append(f"Risk Level: MEDIUM ({intel.risk_score}/100)")
    else:
        notes.append(f"Risk Level: LOW ({intel.risk_score}/100)")
    
    # tactics used
    if intel.tactics_detected:
        notes.append(f"Tactics: {', '.join(intel.tactics_detected)}")
    
    # what was collected
    collected = []
    if intel.upi_ids:
        collected.append(f"{len(set(intel.upi_ids))} UPI ID(s): {', '.join(list(set(intel.upi_ids))[:3])}")
    if intel.phone_numbers:
        collected.append(f"{len(set(intel.phone_numbers))} phone(s)")
    if intel.email_addresses:
        collected.append(f"{len(set(intel.email_addresses))} email(s)")
    if intel.bank_accounts:
        collected.append(f"{len(set(intel.bank_accounts))} account(s)")
    if intel.phishing_links:
        collected.append(f"{len(set(intel.phishing_links))} link(s)")
    if intel.names:
        collected.append(f"Names: {', '.join(list(set(intel.names))[:3])}")
    
    if collected:
        notes.append("Extracted: " + "; ".join(collected))
    
    return ". ".join(notes) if notes else "Scam attempt detected - gathering more intel"


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":
    test_messages = [
        """
        URGENT: Your SBI account 1234567890123 is blocked! 
        Send Rs.100 to verify: scammer@ybl
        Call +91 98765 43210 or WhatsApp 9876543210
        Click http://sbi-verify-kyc.xyz/update
        Share OTP immediately to avoid legal action!
        This is Rajesh Kumar from SBI calling.
        IFSC: SBIN0001234
        """,
        """
        Congratulations! You won Rs.50,00,000 in lottery!
        To claim, transfer processing fee of Rs.5000 to:
        A/C: 9876543210987654
        IFSC: HDFC0001234
        Or send to gaurav.lottery@paytm
        Contact: lottery.winner@gmail.com
        Hurry! Offer expires in 24 hours!
        """,
        """
        आपका खाता ब्लॉक हो गया है! तुरंत OTP भेजें
        UPI: fraud@oksbi
        फोन: 8765432109
        पैसे भेजें: Rs.999
        """
    ]
    
    print("=" * 60)
    print("INTELLIGENCE EXTRACTION TEST")
    print("=" * 60)
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n--- Test Message {i} ---")
        intel = extract_from_text(msg)
        print(f"UPI IDs: {intel.upi_ids}")
        print(f"Phones: {intel.phone_numbers}")
        print(f"Bank Accounts: {intel.bank_accounts}")
        print(f"IFSC Codes: {intel.ifsc_codes}")
        print(f"Emails: {intel.email_addresses}")
        print(f"Links: {intel.phishing_links}")
        print(f"Names: {intel.names}")
        print(f"Amounts: {intel.amounts}")
        print(f"Keywords: {intel.suspicious_keywords}")
        print(f"Tactics: {intel.tactics_detected}")
        print(f"Scam Type: {intel.scam_type}")
        print(f"Risk Score: {intel.risk_score}/100")
        print(f"\nAgent Notes: {generate_agent_notes(intel)}")
