"""
config.py - Centralized configuration using Pydantic Settings

Loads all settings from environment variables with defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # ============================================================
    # APP SETTINGS
    # ============================================================
    APP_NAME: str = "ScamShield API"
    APP_VERSION: str = "4.0.0"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:5500"  # For OAuth redirects
    
    # API Authentication
    API_SECRET_KEY: str = "6dc04eba98e0589d884fa89c6205a24040281175d84762cc14c1e6c8a6e1919e"
    
    # ============================================================
    # DATABASE (MongoDB)
    # ============================================================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "scamshield"
    
    # ============================================================
    # JWT AUTHENTICATION
    # ============================================================
    JWT_SECRET_KEY: str = "f5a6397afdb55272aa28d2b46ca56663875b075a467ebfe4ec649f33ce62119f"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============================================================
    # GOOGLE OAUTH 2.0
    # Get credentials at: https://console.cloud.google.com/apis/credentials
    # ============================================================
    GOOGLE_CLIENT_ID: Optional[str] = "2220501203-54b23quk9dqmh0l3m4bbk0c74d4v5tr1.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: Optional[str] = "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"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # ============================================================
    # GITHUB OAUTH (optional)
    # Get credentials at: https://github.com/settings/developers
    # ============================================================
    GITHUB_CLIENT_ID: Optional[str] = "Ov23liwCq3fCCn0lpFf4"
    GITHUB_CLIENT_SECRET: Optional[str] = "b25930f4852e9aa0e67ad33502c2f4ffb6b848124"
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"
    
    # ============================================================
    # AI PROVIDERS
    # ============================================================
    # Groq - FREE, fast
    GROQ_API_KEY: Optional[str] = "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"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # Google Gemini - FREE tier
    GEMINI_API_KEY: Optional[str] = "AIzaSyCiyfgSO_w7QR7PJKLBjZZR5k66y15rUHA"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # DeepSeek - affordable
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Ollama - FREE, local
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    # Which provider to use
    AI_PROVIDER: str = "auto"  # auto, groq, gemini, deepseek, ollama
    
    # ============================================================
    # CALLBACK SETTINGS (GUVI Hackathon)
    # ============================================================
    GUVI_CALLBACK_URL: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    MIN_MESSAGES_BEFORE_REPORT: int = 6
    AUTO_CALLBACK: bool = True
    
    # ============================================================
    # EMAIL SETTINGS (for password reset, verification)
    # ============================================================
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = "raghavshivam4321@gmail.com"
    SMTP_PASSWORD: Optional[str] = "yzus qevn zhqt uxbb"
    EMAILS_FROM_EMAIL: str = "noreply@scamshield.com"
    EMAILS_FROM_NAME: str = "ScamShield"
    
    # ============================================================
    # CORS SETTINGS
    # ============================================================
    CORS_ORIGINS: List[str] = ["*"]
    
    # ============================================================
    # RATE LIMITING
    # ============================================================
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # ============================================================
    # SUPPORTED LANGUAGES
    # ============================================================
    SUPPORTED_LANGUAGES: List[str] = [
        "en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Use this instead of creating new Settings() each time.
    """
    return Settings()


# Global settings instance
settings = get_settings()
