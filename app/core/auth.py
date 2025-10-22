from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import TokenData, decode_token
from app.core.config import settings
from app.db.database import get_db
from app.db import models
from app.core.security_utils import sanitize_input
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# OAuth2 scheme with proper URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Function to get current user from token
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = decode_token(token)
        
        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # Sanitize data from token
        email = sanitize_input(email)
        role: str = sanitize_input(payload.get("role", ""))
        
        token_data = TokenData(email=email, role=role, sub=email)
        
        # Add token data to request state for logging and auditing
        request.state.user_email = email
        request.state.user_role = role
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database using parameterized query to prevent SQL injection
    try:
        user = db.query(models.User).filter(models.User.email == token_data.email).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Add user ID to request state for logging
        request.state.user_id = user.id
        
        return user
    except Exception as e:
        # Log database access errors but don't expose details
        print(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Function to get current active user
async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Verify that the current user is active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user

# Function to get current admin user
async def get_admin_user(request: Request, current_user = Depends(get_current_user)):
    """
    Verify that the current user is an admin
    """
    if current_user.role != "admin":
        # Log access attempt for auditing
        client_ip = request.client.host if request.client else "unknown"
        print(f"Unauthorized admin access attempt by user {current_user.id} from {client_ip}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have sufficient permissions to perform this action"
        )
    return current_user

# Function to get current instructor or admin user
async def get_instructor_or_admin_user(request: Request, current_user = Depends(get_current_user)):
    """
    Verify that the current user is an instructor or admin
    """
    if current_user.role not in ["admin", "instructor"]:
        # Log access attempt for auditing
        client_ip = request.client.host if request.client else "unknown"
        print(f"Unauthorized instructor access attempt by user {current_user.id} from {client_ip}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have sufficient permissions to perform this action"
        )
    return current_user

# Function to verify resource ownership
async def verify_resource_owner(
    resource_id: int, 
    resource_type: str,
    user_id: int,
    db: Session = Depends(get_db)
) -> bool:
    """
    Verify that the current user owns the requested resource
    """
    if resource_type == "course":
        resource = db.query(models.Course).filter(models.Course.id == resource_id).first()
        return resource and resource.instructor_id == user_id
    elif resource_type == "blog":
        resource = db.query(models.BlogPost).filter(models.BlogPost.id == resource_id).first()
        return resource and resource.author_id == user_id
    
    return False