"""
validators.py - Input validation utilities
"""

import re
from typing import Optional, List, Tuple
from pydantic import validator, field_validator


class PasswordValidator:
    """
    Password strength validator with configurable rules.
    """
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Common weak passwords to reject
    COMMON_PASSWORDS = {
        "password", "123456", "12345678", "qwerty", "abc123",
        "monkey", "1234567", "letmein", "trustno1", "dragon",
        "baseball", "iloveyou", "master", "sunshine", "ashley",
        "football", "shadow", "123123", "654321", "password1"
    }
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not password:
            return False, ["Password is required"]
        
        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")
        
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must be at most {cls.MAX_LENGTH} characters")
        
        # Uppercase check
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Digit check
        if cls.REQUIRE_DIGIT and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        # Special character check
        if cls.REQUIRE_SPECIAL and not re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password):
            errors.append(f"Password must contain at least one special character ({cls.SPECIAL_CHARS})")
        
        # Common password check
        if password.lower() in cls.COMMON_PASSWORDS:
            errors.append("This password is too common. Please choose a stronger password.")
        
        # Check for repeated characters
        if re.search(r"(.)\1{3,}", password):
            errors.append("Password cannot contain more than 3 repeated characters")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_strength_score(cls, password: str) -> dict:
        """
        Calculate password strength score (0-100).
        
        Returns:
            dict with score, strength label, and suggestions
        """
        if not password:
            return {"score": 0, "strength": "none", "suggestions": ["Enter a password"]}
        
        score = 0
        suggestions = []
        
        # Length score (up to 30 points)
        length_score = min(len(password) * 2, 30)
        score += length_score
        
        if len(password) < 12:
            suggestions.append("Use at least 12 characters for better security")
        
        # Character variety (up to 40 points)
        if re.search(r"[a-z]", password):
            score += 10
        else:
            suggestions.append("Add lowercase letters")
        
        if re.search(r"[A-Z]", password):
            score += 10
        else:
            suggestions.append("Add uppercase letters")
        
        if re.search(r"\d", password):
            score += 10
        else:
            suggestions.append("Add numbers")
        
        if re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password):
            score += 10
        else:
            suggestions.append("Add special characters")
        
        # Bonus for mixing (up to 20 points)
        char_types = sum([
            bool(re.search(r"[a-z]", password)),
            bool(re.search(r"[A-Z]", password)),
            bool(re.search(r"\d", password)),
            bool(re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password))
        ])
        score += char_types * 5
        
        # Penalty for common patterns
        if password.lower() in cls.COMMON_PASSWORDS:
            score = min(score, 10)
            suggestions.append("Avoid common passwords")
        
        if re.search(r"(.)\1{2,}", password):
            score -= 10
            suggestions.append("Avoid repeated characters")
        
        # Determine strength label
        if score >= 80:
            strength = "strong"
        elif score >= 60:
            strength = "good"
        elif score >= 40:
            strength = "fair"
        elif score >= 20:
            strength = "weak"
        else:
            strength = "very_weak"
        
        return {
            "score": min(max(score, 0), 100),
            "strength": strength,
            "suggestions": suggestions[:3]  # Top 3 suggestions
        }


class EmailValidator:
    """Email validation utilities."""
    
    # Disposable email domains to reject
    DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwaway.com", "mailinator.com", "guerrillamail.com",
        "10minutemail.com", "yopmail.com", "trashmail.com", "fakeinbox.com"
    }
    
    @classmethod
    def is_disposable(cls, email: str) -> bool:
        """Check if email is from a disposable email service."""
        try:
            domain = email.lower().split("@")[1]
            return domain in cls.DISPOSABLE_DOMAINS
        except (IndexError, AttributeError):
            return False
    
    @classmethod
    def validate(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format and check for disposable domains.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic format check
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        # Check for disposable email
        if cls.is_disposable(email):
            return False, "Disposable email addresses are not allowed"
        
        return True, None


class PhoneValidator:
    """Phone number validation utilities."""
    
    @classmethod
    def validate_indian(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Indian phone number.
        
        Accepts formats:
        - 9876543210
        - +919876543210
        - 91-9876543210
        - +91-9876543210
        """
        if not phone:
            return True, None  # Phone is optional
        
        # Remove common separators
        clean_phone = re.sub(r"[-\s()]", "", phone)
        
        # Check various Indian phone formats
        patterns = [
            r"^[6-9]\d{9}$",           # 10 digit starting with 6-9
            r"^91[6-9]\d{9}$",         # With 91 prefix
            r"^\+91[6-9]\d{9}$",       # With +91 prefix
        ]
        
        for pattern in patterns:
            if re.match(pattern, clean_phone):
                return True, None
        
        return False, "Invalid Indian phone number format"
    
    @classmethod
    def normalize(cls, phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format."""
        if not phone:
            return phone
        
        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)
        
        # Handle various formats
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        elif len(digits) == 11 and digits.startswith("0"):
            return f"+91{digits[1:]}"
        
        return phone  # Return as-is if can't normalize


# ============================================================
# PYDANTIC VALIDATORS (for use in schemas)
# ============================================================

def validate_password_strength(password: str) -> str:
    """Pydantic validator for password strength."""
    is_valid, errors = PasswordValidator.validate(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password


def validate_email_not_disposable(email: str) -> str:
    """Pydantic validator to reject disposable emails."""
    is_valid, error = EmailValidator.validate(email)
    if not is_valid:
        raise ValueError(error)
    return email.lower()


def validate_indian_phone(phone: Optional[str]) -> Optional[str]:
    """Pydantic validator for Indian phone numbers."""
    if not phone:
        return phone
    
    is_valid, error = PhoneValidator.validate_indian(phone)
    if not is_valid:
        raise ValueError(error)
    
    return PhoneValidator.normalize(phone)
