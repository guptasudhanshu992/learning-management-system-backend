from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.security_utils import sanitize_input, validate_password_strength

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token data model
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    sub: Optional[str] = None

# Function to verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password: str) -> str:
    """
    Hash a password for storage
    """
    # First validate password strength
    validation = validate_password_strength(password)
    if not validation["valid"]:
        raise ValueError(validation["message"])
    
    return pwd_context.hash(password)

# Function to create access token
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access", "iat": datetime.utcnow()})
    
    # Sanitize input data if it contains strings
    for key, value in to_encode.items():
        if isinstance(value, str):
            to_encode[key] = sanitize_input(value)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Function to create refresh token
def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.utcnow()})
    
    # Sanitize input data if it contains strings
    for key, value in to_encode.items():
        if isinstance(value, str):
            to_encode[key] = sanitize_input(value)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )