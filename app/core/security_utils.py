import bleach
from typing import Any, Dict, List, Union
import re
from sqlalchemy.sql import text

def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS attacks
    """
    if value is None:
        return None
    
    # Use bleach to clean HTML tags
    return bleach.clean(
        value, 
        tags=[],  # No HTML tags allowed
        strip=True
    )

def sanitize_rich_text(value: str) -> str:
    """
    Sanitize rich text input but allow some safe HTML tags
    """
    if value is None:
        return None
    
    # Use bleach to clean HTML tags but allow some safe ones
    return bleach.clean(
        value,
        tags=['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
              'ul', 'ol', 'li', 'blockquote', 'code', 'pre'],
        attributes={
            '*': ['class', 'style'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        },
        styles=['text-align', 'font-weight', 'text-decoration', 'color', 'background-color'],
        strip=True
    )

def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value)
        else:
            sanitized[key] = value
            
    return sanitized

def sanitize_list(data: List[Any]) -> List[Any]:
    """
    Recursively sanitize all string values in a list
    """
    sanitized = []
    
    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_input(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item))
        else:
            sanitized.append(item)
            
    return sanitized

def safe_sql_query(query: str, params: Dict[str, Any] = None) -> str:
    """
    Create a safe SQL query using parameterization
    """
    # Never use string formatting or concatenation for SQL queries
    # Always use parameterized queries with sqlalchemy text()
    return text(query), params

def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    Validate password strength based on security settings
    """
    from app.core.config import settings
    
    # Check length
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return {"valid": False, "message": f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long"}
    
    # Check for uppercase letter
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return {"valid": False, "message": "Password must contain at least one uppercase letter"}
    
    # Check for lowercase letter
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return {"valid": False, "message": "Password must contain at least one lowercase letter"}
    
    # Check for digit
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return {"valid": False, "message": "Password must contain at least one digit"}
    
    # Check for special character
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return {"valid": False, "message": "Password must contain at least one special character"}
    
    # Check for common passwords
    if password.lower() in ["password", "123456", "qwerty", "admin", "welcome", "password123"]:
        return {"valid": False, "message": "This password is too common and easily guessed"}
    
    # Check for sequential characters
    if re.search(r"abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789|987|876|765|654|543|432|321|210", password.lower()):
        return {"valid": False, "message": "Password contains sequential characters"}
    
    # Check for repeated characters
    if re.search(r"(.)\1{2,}", password):
        return {"valid": False, "message": "Password contains too many repeated characters"}
    
    return {"valid": True, "message": "Password is strong"}