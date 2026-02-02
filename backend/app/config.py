"""
config.py - loads environment variables

simplified - only providers with API keys:
- Groq (FREE, fast) - API key provided
- Gemini (FREE tier) - API key provided
- Ollama (FREE, local) - no key needed
"""

import os
from dotenv import load_dotenv

load_dotenv()

# api auth key - requests without this get rejected
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "change-me-in-production")

# --- AI Provider Keys ---

# groq - FREE, super fast
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# google gemini - FREE tier
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# deepseek - affordable, powerful
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ollama - FREE, local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# which provider to use (auto = try groq first, then gemini, then ollama)
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto")

# --- Callback Settings ---
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
MIN_MESSAGES_BEFORE_REPORT = 6
AUTO_CALLBACK = os.getenv("AUTO_CALLBACK", "true").lower() == "true"

# --- Language Settings ---
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa"]

# log level
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# sanity check on startup
def check_config():
    providers = []
    if GROQ_API_KEY: providers.append("Groq")
    if GEMINI_API_KEY: providers.append("Gemini")
    if DEEPSEEK_API_KEY: providers.append("DeepSeek")
    providers.append("Ollama (local)")
    
    print(f"[CONFIG] AI providers configured: {', '.join(providers)}")
    return len(providers) > 0

check_config()
