from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List
from sqlalchemy import func

from app.db.database import get_db
from app.db import models
from app.schemas.user import (
    UserResponse, UserUpdate, UserUpdatePassword, 
    UserAdminCreate, UserAdminUpdate
)
from app.core.security import verify_password, get_password_hash
from app.core.auth import get_current_active_user, get_admin_user

# Create router
router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user
    """
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Update current user
    """
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.put("/me/password", status_code=status.HTTP_200_OK)
def update_password(
    password_update: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Update current user password
    """
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

# Admin endpoints
@router.get("", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, min_length=3),
    role: str = Query(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> Any:
    """
    Get all users (admin only)
    """
    query = db.query(models.User)
    
    # Apply filters
    if search:
        query = query.filter(
            (models.User.first_name.ilike(f"%{search}%")) |
            (models.User.last_name.ilike(f"%{search}%")) |
            (models.User.email.ilike(f"%{search}%"))
        )
    
    if role:
        query = query.filter(models.User.role == role)
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserAdminCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> Any:
    """
    Create new user (admin only)
    """
    # Check if user with this email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = models.User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        is_active=user.is_active
    )
    
    # Add to DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> Any:
    """
    Get user by ID (admin only)
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user_admin(
    user_id: int,
    user_update: UserAdminUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> Any:
    """
    Update user (admin only)
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> None:
    """
    Delete user (admin only)
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()