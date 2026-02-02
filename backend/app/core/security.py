"""
security.py - Password hashing and JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import bcrypt

from jose import JWTError, jwt

from app.core.config import settings


# ============================================================
# PASSWORD HASHING (using bcrypt directly for Python 3.13 compatibility)
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    # Encode password and generate salt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ============================================================
# JWT TOKEN MANAGEMENT
# ============================================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Usually the user ID
        expires_delta: Custom expiration time
        additional_claims: Extra data to include in token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Usually the user ID
        expires_delta: Custom expiration time
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Returns:
        Token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiry time from a token.
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


# ============================================================
# TOKEN GENERATION UTILITIES
# ============================================================

def generate_verification_token() -> str:
    """
    Generate a random token for email verification.
    """
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """
    Generate a random token for password reset.
    """
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """
    Generate a new API key.
    """
    return secrets.token_urlsafe(48)


# ============================================================
# FINGERPRINT HASHING
# ============================================================

def create_scammer_fingerprint_hash(identifiers: list) -> str:
    """
    Create a hash from scammer identifiers for fingerprinting.
    """
    # Sort and join identifiers for consistent hashing
    sorted_ids = sorted([str(i).lower().strip() for i in identifiers if i])
    combined = "|".join(sorted_ids)
    
    return hashlib.sha256(combined.encode()).hexdigest()
