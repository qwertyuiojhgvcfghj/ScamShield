"""
language_detector.py

detects language of incoming messages.
uses simple keyword detection + optional langdetect library.

supports: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi
"""

import re

# common words in different languages for quick detection
LANG_MARKERS = {
    "hi": [  # Hindi
        "आप", "है", "हैं", "में", "को", "का", "की", "के", "और", "से",
        "क्या", "कृपया", "अभी", "तुरंत", "बैंक", "खाता", "पैसे", "रुपये",
        "ओटीपी", "लिंक", "क्लिक", "वेरिफाई", "ब्लॉक", "सस्पेंड"
    ],
    "ta": [  # Tamil
        "நீங்கள்", "என்ன", "இது", "உங்கள்", "வங்கி", "கணக்கு", "பணம்",
        "உடனடியாக", "சரிபார்க்க", "கிளிக்", "லிங்க்", "ஓடிபி"
    ],
    "te": [  # Telugu
        "మీరు", "మీ", "బ్యాంక్", "ఖాతా", "డబ్బు", "వెంటనే", "క్లిక్",
        "లింక్", "ఓటీపీ", "వెరిఫై"
    ],
    "kn": [  # Kannada
        "ನೀವು", "ನಿಮ್ಮ", "ಬ್ಯಾಂಕ್", "ಖಾತೆ", "ಹಣ", "ತಕ್ಷಣ", "ಕ್ಲಿಕ್",
        "ಲಿಂಕ್", "ಒಟಿಪಿ", "ವೆರಿಫೈ"
    ],
    "ml": [  # Malayalam
        "നിങ്ങൾ", "നിങ്ങളുടെ", "ബാങ്ക്", "അക്കൌണ്ട്", "പണം", "ഉടനെ",
        "ക്ലിക്ക്", "ലിങ്ക്", "ഒടിപി", "വെരിഫൈ"
    ],
    "bn": [  # Bengali
        "আপনি", "আপনার", "ব্যাংক", "অ্যাকাউন্ট", "টাকা", "এখনই",
        "ক্লিক", "লিংক", "ওটিপি", "ভেরিফাই"
    ],
    "mr": [  # Marathi
        "तुम्ही", "तुमचा", "बँक", "खाते", "पैसे", "आता", "लगेच",
        "क्लिक", "लिंक", "ओटीपी", "व्हेरिफाय"
    ],
    "gu": [  # Gujarati
        "તમે", "તમારું", "બેંક", "ખાતું", "પૈસા", "હમણાં", "તરત",
        "ક્લિક", "લિંક", "ઓટીપી", "વેરિફાય"
    ],
    "pa": [  # Punjabi
        "ਤੁਸੀਂ", "ਤੁਹਾਡਾ", "ਬੈਂਕ", "ਖਾਤਾ", "ਪੈਸੇ", "ਹੁਣੇ", "ਤੁਰੰਤ",
        "ਕਲਿੱਕ", "ਲਿੰਕ", "ਓਟੀਪੀ", "ਵੈਰੀਫਾਈ"
    ]
}

# script-based detection (more reliable for indian languages)
SCRIPT_PATTERNS = {
    "hi": r'[\u0900-\u097F]',  # Devanagari (Hindi, Marathi)
    "ta": r'[\u0B80-\u0BFF]',  # Tamil
    "te": r'[\u0C00-\u0C7F]',  # Telugu
    "kn": r'[\u0C80-\u0CFF]',  # Kannada
    "ml": r'[\u0D00-\u0D7F]',  # Malayalam
    "bn": r'[\u0980-\u09FF]',  # Bengali
    "gu": r'[\u0A80-\u0AFF]',  # Gujarati
    "pa": r'[\u0A00-\u0A7F]',  # Punjabi (Gurmukhi)
}


def detect_language(text):
    """
    detect language of text
    
    returns language code (en, hi, ta, te, etc.)
    """
    if not text:
        return "en"
    
    # first check script patterns (most reliable for indian langs)
    for lang, pattern in SCRIPT_PATTERNS.items():
        if re.search(pattern, text):
            # check for marathi vs hindi (both use devanagari)
            if lang == "hi" and any(word in text for word in ["तुम्ही", "आहे", "मराठी"]):
                return "mr"
            return lang
    
    # check for language markers
    text_lower = text.lower()
    for lang, markers in LANG_MARKERS.items():
        matches = sum(1 for m in markers if m in text_lower or m in text)
        if matches >= 2:
            return lang
    
    # default to english
    return "en"


def get_language_name(code):
    """get full language name from code"""
    names = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "pa": "Punjabi"
    }
    return names.get(code, "English")


# test
if __name__ == "__main__":
    tests = [
        "Your account is blocked",
        "आपका खाता ब्लॉक हो गया है",
        "உங்கள் கணக்கு தடுக்கப்பட்டுள்ளது",
        "మీ ఖాతా బ్లాక్ చేయబడింది",
        "ನಿಮ್ಮ ಖಾತೆ ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ",
    ]
    
    for t in tests:
        lang = detect_language(t)
        print(f"{get_language_name(lang)}: {t[:30]}...")
