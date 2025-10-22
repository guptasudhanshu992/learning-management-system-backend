from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.schemas.ecommerce import (
    CartItemCreate, CartResponse, CartItemResponse
)
from app.core.auth import get_current_active_user

# Create router
router = APIRouter()

@router.get("", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's cart
    """
    # Get cart items
    cart_items = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).all()
    
    # Format response
    items = []
    total_price = 0
    
    for item in cart_items:
        course = db.query(models.Course).filter(models.Course.id == item.course_id).first()
        if course:
            # Calculate price (use discount price if available)
            price = course.discount_price if course.discount_price else course.price
            total_price += price
            
            # Format cart item
            item_response = CartItemResponse(
                id=item.id,
                user_id=current_user.id,
                course_id=course.id,
                course_title=course.title,
                course_price=course.price,
                course_discount_price=course.discount_price,
                course_thumbnail=course.thumbnail,
                added_at=item.added_at
            )
            
            items.append(item_response)
    
    return {
        "items": items,
        "total_price": total_price,
        "total_items": len(items)
    }

@router.post("", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Add item to cart
    """
    # Check if course exists
    course = db.query(models.Course).filter(models.Course.id == item.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is already enrolled in the course
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == item.course_id,
        models.Enrollment.user_id == current_user.id
    ).first()
    
    if enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course"
        )
    
    # Check if course is already in cart
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.course_id == item.course_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already in cart"
        )
    
    # Create new cart item
    new_cart_item = models.CartItem(
        course_id=item.course_id,
        user_id=current_user.id,
        added_at=datetime.utcnow()
    )
    
    # Add to DB
    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)
    
    # Format response
    return CartItemResponse(
        id=new_cart_item.id,
        user_id=current_user.id,
        course_id=course.id,
        course_title=course.title,
        course_price=course.price,
        course_discount_price=course.discount_price,
        course_thumbnail=course.thumbnail,
        added_at=new_cart_item.added_at
    )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> None:
    """
    Remove item from cart
    """
    # Get cart item
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    # Delete cart item
    db.delete(cart_item)
    db.commit()