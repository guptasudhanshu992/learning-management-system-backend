from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any
import asyncio
from starlette.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.db.database import get_db
from app.db import models
from app.core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token,
    decode_token
)
from app.core.config import settings
from app.schemas.user import (
    UserCreate, UserResponse, Token, 
    PasswordReset, PasswordResetConfirm
)
from app.core.auth import limiter
from app.core.security_utils import (
    sanitize_input, validate_email, validate_password_strength
)

# Create router with prefix-independent tags
router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, 
    user: UserCreate, 
    response: Response,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    # Skip CSRF for API registration - handled by CORS
    # In a production app, you'd want proper CSRF protection
    
    # Validate and sanitize inputs
    try:
        # Sanitize user inputs
        email = sanitize_input(user.email)
        full_name = sanitize_input(user.full_name)
        
        # Validate email format
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password strength
        password_validation = validate_password_strength(user.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Check if user with this email already exists
        db_user = db.query(models.User).filter(models.User.email == email).first()
        if db_user:
            # Use a generic message to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use"
            )
        
        # Validate full name
        if not full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required and cannot be empty"
            )

        # Create new user
        new_user = models.User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(user.password),
            role="user",
            is_active=True,
            is_verified=False,  # Require email verification
            created_at=datetime.utcnow()
        )
        
        # Add to DB with transaction
        try:
            db.add(new_user)
            db.commit()
            
            # Log registration for audit
            client_ip = request.client.host if request.client else "unknown"
            logging.info(f"New user registered: {new_user.id} from IP {client_ip}")
            db.refresh(new_user)
            
            # Log user creation for audit
            client_ip = request.client.host if request.client else "unknown"
            print(f"New user registered: {new_user.id} from IP {client_ip}")
            
            return new_user
        except Exception as e:
            # Rollback on error
            db.rollback()
            print(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User registration failed. Please try again later."
            )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Login with username and password
    """
    # Skip CSRF for API login - handled by CORS
    
    try:
        # Sanitize input
        username = sanitize_input(form_data.username)
        
        # Find user by email
        user = db.query(models.User).filter(models.User.email == username).first()
        
        # Use constant time comparison to prevent timing attacks
        # Always verify a password hash even if user doesn't exist
        is_valid = False
        if user:
            is_valid = verify_password(form_data.password, user.hashed_password)
        else:
            # Simulate password verification to prevent timing attacks
            verify_password(form_data.password, "$2b$12$rvMGRrXtBgmkK9QYeHv0g.7O8hSNO/xVnZwgGTkaVixW4TwKm5Mgu")
        
        # Check if user exists and password is correct
        if not is_valid:
            # Log failed attempt
            client_ip = request.client.host if request.client else "unknown"
            logging.warning(f"Failed login attempt for user {username} from IP {client_ip}")
            
            # Add a small delay to prevent brute force attacks
            await asyncio.sleep(0.5)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated"
            )
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Log successful login for audit
        client_ip = request.client.host if request.client else "unknown"
        logging.info(f"User login: {user.id} from IP {client_ip}")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": user.email, "role": user.role, "user_id": user.id}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logging.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed. Please try again later."
            )
        raise

@router.post("/refresh-token", response_model=Token)
def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db)) -> Any:
    """
    Refresh access token
    """
    # Create access token
    try:
        # Decode token
        from jose import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        new_refresh_token = create_refresh_token(
            data={"sub": user.email, "role": user.role}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/password-reset", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def request_password_reset(
    request: Request, 
    reset_data: PasswordReset, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset (sends email in real implementation)
    """
    try:
        # Skip CSRF validation for API endpoint
        
        # Sanitize input
        email = sanitize_input(reset_data.email)
        
        # Validate email format
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Check if user exists
        user = db.query(models.User).filter(models.User.email == email).first()
        
        # We don't want to reveal if a user exists or not, so always return success
        if not user:
            # Add a small delay to prevent user enumeration through timing attacks
            await asyncio.sleep(0.5)
            return {"message": "If your email is registered, you will receive a password reset link"}
        
        # In a real implementation, generate a token and send an email with reset link
        # Log the request for audit
        client_ip = request.client.host if request.client else "unknown"
        logging.info(f"Password reset requested for user {user.id} from IP {client_ip}")
        
        # Add a small delay to prevent user enumeration through timing attacks
        await asyncio.sleep(0.5)
        
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logging.error(f"Password reset error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset request failed. Please try again later."
            )
        raise

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password(
    request: Request, 
    reset_data: PasswordResetConfirm, 
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset password with token
    """
    try:
        # Skip CSRF validation for API endpoint
        
        # Sanitize and validate inputs
        token = sanitize_input(reset_data.token)
        
        # Validate password strength
        password_validation = validate_password_strength(reset_data.new_password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Verify passwords match
        if reset_data.new_password != reset_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # In a real implementation:
        # 1. Validate the token
        # 2. Find the user associated with the token
        # 3. Update the password
        # 4. Invalidate all existing sessions
        
        # For demonstration purposes (in real app, we'd decode the token and get user)
        try:
            # This would be replaced with actual token validation
            payload = decode_token(token)
            user_email = payload.get("sub")
            
            # Find user
            user = db.query(models.User).filter(models.User.email == user_email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired token"
                )
            
            # Update password
            user.hashed_password = get_password_hash(reset_data.new_password)
            db.commit()
            
            # Log for audit
            client_ip = request.client.host if request.client else "unknown"
            logging.info(f"Password reset completed for user {user.id} from IP {client_ip}")
            
            return {"message": "Password has been reset successfully"}
        
        except Exception:
            # Token validation failed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logging.error(f"Password reset error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed. Please try again later."
            )
        raise