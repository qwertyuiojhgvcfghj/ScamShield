"""
factual_answers.py

FREE factual-answering using DuckDuckGo and Wikipedia APIs.
no API keys needed!

used by the honeypot agent to answer factual questions
from scammers, making responses more believable.

APIs used:
- DuckDuckGo Instant Answer API (free, no key)
- Wikipedia REST API (free, no key)
"""

import re
import requests
from typing import Optional
from urllib.parse import quote


# timeout for API requests (seconds)
REQUEST_TIMEOUT = 5


# ============================================================
# FACTUAL QUESTION DETECTION
# ============================================================

# patterns that indicate factual questions
FACTUAL_PATTERNS = [
    r'\b(what|who|where|when|which)\s+(is|are|was|were)\b',
    r'\b(what|who|where|when|which)\s+\w+\s+(is|are|was|were)\b',
    r'\bhow\s+(do|does|did|is|are|can|to|many|much)\b',
    r'\bwhy\s+(is|are|do|does|did|was|were)\b',
    r'\b(define|meaning\s+of|definition\s+of)\b',
    r'\bwhat\s+does\s+\w+\s+mean\b',
    r'\btell\s+me\s+about\b',
    r'\bexplain\s+(what|how|why)\b',
    r'\bdo\s+you\s+know\s+(what|who|where|when|why|how)\b',
    # hindi patterns
    r'\b(kya|kaun|kahan|kab|kyun|kaise)\s+hai\b',
    r'\bये\s+क्या\s+है\b',
    r'\bक्या\s+है\b',
]

# compile patterns for efficiency
FACTUAL_REGEX = [re.compile(p, re.IGNORECASE) for p in FACTUAL_PATTERNS]


def is_factual_question(text: str) -> bool:
    """
    detect if text is asking a factual question.
    
    examples that return True:
    - "What is UPI?"
    - "How does bank transfer work?"
    - "Who is the RBI governor?"
    - "Define cryptocurrency"
    """
    text = text.strip()
    
    # must have question-like structure
    if not text:
        return False
    
    # check against patterns
    for pattern in FACTUAL_REGEX:
        if pattern.search(text):
            return True
    
    # check for question mark with common question starters
    if '?' in text:
        starters = ['what', 'who', 'where', 'when', 'why', 'how', 'which', 'can', 'is', 'are', 'do', 'does']
        first_word = text.split()[0].lower().rstrip('?')
        if first_word in starters:
            return True
    
    return False


def extract_query_topic(text: str) -> str:
    """
    extract the main topic from a question.
    
    "What is UPI?" -> "UPI"
    "How does cryptocurrency work?" -> "cryptocurrency"
    "Tell me about Bitcoin" -> "Bitcoin"
    """
    text = text.strip().rstrip('?').rstrip('.')
    
    # patterns to extract topic
    patterns = [
        r'what\s+is\s+(?:a\s+|an\s+|the\s+)?(.+)',
        r'who\s+is\s+(.+)',
        r'where\s+is\s+(.+)',
        r'what\s+are\s+(.+)',
        r'how\s+does\s+(.+?)(?:\s+work)?',
        r'how\s+do\s+(.+?)(?:\s+work)?',
        r'tell\s+me\s+about\s+(.+)',
        r'define\s+(.+)',
        r'meaning\s+of\s+(.+)',
        r'explain\s+(.+)',
        r'what\s+does\s+(.+?)\s+mean',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # fallback: return text without common prefixes
    text = re.sub(r'^(what|who|where|when|why|how|is|are|the|a|an)\s+', '', text, flags=re.IGNORECASE)
    return text.strip()


# ============================================================
# DUCKDUCKGO INSTANT ANSWER API
# ============================================================

def duckduckgo_search(query: str) -> Optional[str]:
    """
    search DuckDuckGo Instant Answer API.
    returns abstract text if available, else None.
    
    FREE - no API key needed!
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # try AbstractText first (main summary)
        abstract = data.get("AbstractText", "").strip()
        if abstract and len(abstract) > 20:
            return _clean_and_shorten(abstract)
        
        # try Answer field (for calculations, conversions)
        answer = data.get("Answer", "").strip()
        if answer:
            return _clean_and_shorten(answer)
        
        # try Definition
        definition = data.get("Definition", "").strip()
        if definition:
            return _clean_and_shorten(definition)
        
        # try first RelatedTopic
        related = data.get("RelatedTopics", [])
        if related and isinstance(related, list) and len(related) > 0:
            first = related[0]
            if isinstance(first, dict) and first.get("Text"):
                return _clean_and_shorten(first["Text"])
        
        return None
        
    except Exception as e:
        print(f"[DDG] Error: {e}")
        return None


# ============================================================
# WIKIPEDIA API
# ============================================================

def wikipedia_summary(title: str) -> Optional[str]:
    """
    get Wikipedia summary for a specific page title.
    
    FREE - no API key needed!
    """
    try:
        # URL encode the title
        encoded_title = quote(title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        
        headers = {
            "User-Agent": "HoneypotBot/1.0 (Educational Project)"
        }
        
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # get extract (summary)
        extract = data.get("extract", "").strip()
        if extract and len(extract) > 20:
            return _clean_and_shorten(extract)
        
        return None
        
    except Exception as e:
        print(f"[WIKI] Summary error: {e}")
        return None


def wiki_search_and_summary(query: str) -> Optional[str]:
    """
    search Wikipedia for a query, then get summary of best result.
    
    useful when exact title is unknown.
    """
    try:
        # first, search for the query
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1,  # just get first result
        }
        
        headers = {
            "User-Agent": "HoneypotBot/1.0 (Educational Project)"
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # get first search result
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
        
        # get the title of first result
        title = search_results[0].get("title")
        if not title:
            return None
        
        # now get summary for that title
        return wikipedia_summary(title)
        
    except Exception as e:
        print(f"[WIKI] Search error: {e}")
        return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _clean_and_shorten(text: str, max_sentences: int = 2) -> str:
    """
    clean text and limit to max_sentences.
    removes markdown, links, extra whitespace.
    """
    if not text:
        return ""
    
    # remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # remove plain URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # remove markdown formatting
    text = re.sub(r'[*_`#]', '', text)
    
    # normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # split into sentences and take first few
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > max_sentences:
        text = ' '.join(sentences[:max_sentences])
    
    return text.strip()


# ============================================================
# MAIN ROUTER FUNCTION
# ============================================================

def get_factual_answer(message_text: str) -> Optional[str]:
    """
    main function to get factual answer for a message.
    
    logic:
    1. check if it's a factual question
    2. try DuckDuckGo first
    3. if no result, try Wikipedia
    4. return None if nothing found
    
    returns clean, short answer ready to be humanized.
    """
    
    # step 1: check if factual question
    if not is_factual_question(message_text):
        return None
    
    # extract the topic/query
    query = extract_query_topic(message_text)
    if not query or len(query) < 2:
        return None
    
    print(f"[FACTUAL] Query: '{query}'")
    
    # step 2: try DuckDuckGo first (faster)
    answer = duckduckgo_search(query)
    if answer:
        print(f"[FACTUAL] Found via DuckDuckGo")
        return answer
    
    # step 3: try Wikipedia
    answer = wiki_search_and_summary(query)
    if answer:
        print(f"[FACTUAL] Found via Wikipedia")
        return answer
    
    # step 4: nothing found
    print(f"[FACTUAL] No answer found for '{query}'")
    return None


def get_humanized_factual_answer(message_text: str) -> Optional[str]:
    """
    get factual answer wrapped in a human-like response.
    suitable for honeypot agent replies.
    """
    answer = get_factual_answer(message_text)
    
    if not answer:
        return None
    
    # humanize the response (casual, not encyclopedic)
    prefixes = [
        "I think it's something like this — ",
        "Oh I know this one — ",
        "Hmm I remember reading that ",
        "I think ",
        "From what I know, ",
        "I heard that ",
    ]
    
    import random
    prefix = random.choice(prefixes)
    
    return f"{prefix}{answer}"


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    test_questions = [
        "What is UPI?",
        "How does cryptocurrency work?",
        "Who is the prime minister of India?",
        "What is phishing?",
        "Define blockchain",
        "Tell me about RBI",
        "What is your name?",  # not factual
        "Send me money",  # not factual
        "How much is 5 dollars in rupees?",
    ]
    
    print("Testing factual answer system...\n")
    
    for q in test_questions:
        print(f"Q: {q}")
        print(f"   Is factual? {is_factual_question(q)}")
        
        if is_factual_question(q):
            answer = get_humanized_factual_answer(q)
            if answer:
                print(f"   A: {answer[:100]}...")
            else:
                print(f"   A: (no answer found)")
        print()
