from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.db.database import get_db
from app.db import models
from app.schemas.ecommerce import (
    WishlistItemCreate, WishlistItemResponse, WishlistResponse
)
from app.core.auth import get_current_active_user

# Create router
router = APIRouter()

@router.get("", response_model=WishlistResponse)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's wishlist
    """
    # Get wishlist items
    wishlist_items = []
    
    # Get wishlist from the association table
    wishlist_entries = db.query(models.wishlist).filter(
        models.wishlist.c.user_id == current_user.id
    ).all()
    
    for entry in wishlist_entries:
        course_id = entry[1]  # course_id is the second column
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        
        if course:
            # Calculate rating
            rating = db.query(models.Review).filter(models.Review.course_id == course.id).all()
            avg_rating = sum([r.rating for r in rating]) / len(rating) if rating else None
            
            # Format wishlist item
            item = WishlistItemResponse(
                user_id=current_user.id,
                course_id=course.id,
                course_title=course.title,
                course_price=course.price,
                course_discount_price=course.discount_price,
                course_thumbnail=course.thumbnail,
                course_rating=avg_rating
            )
            
            wishlist_items.append(item)
    
    return {
        "items": wishlist_items,
        "total_items": len(wishlist_items)
    }

@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    item: WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Add item to wishlist
    """
    # Check if course exists
    course = db.query(models.Course).filter(models.Course.id == item.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is already in wishlist
    wishlist_item = db.query(models.wishlist).filter(
        models.wishlist.c.course_id == item.course_id,
        models.wishlist.c.user_id == current_user.id
    ).first()
    
    if wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already in wishlist"
        )
    
    # Add to wishlist
    stmt = models.wishlist.insert().values(
        user_id=current_user.id,
        course_id=item.course_id
    )
    db.execute(stmt)
    db.commit()
    
    # Calculate rating
    rating = db.query(models.Review).filter(models.Review.course_id == course.id).all()
    avg_rating = sum([r.rating for r in rating]) / len(rating) if rating else None
    
    # Format response
    return WishlistItemResponse(
        user_id=current_user.id,
        course_id=course.id,
        course_title=course.title,
        course_price=course.price,
        course_discount_price=course.discount_price,
        course_thumbnail=course.thumbnail,
        course_rating=avg_rating
    )

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> None:
    """
    Remove item from wishlist
    """
    # Check if course is in wishlist
    wishlist_item = db.query(models.wishlist).filter(
        models.wishlist.c.course_id == course_id,
        models.wishlist.c.user_id == current_user.id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found in wishlist"
        )
    
    # Remove from wishlist
    stmt = models.wishlist.delete().where(
        (models.wishlist.c.course_id == course_id) & 
        (models.wishlist.c.user_id == current_user.id)
    )
    db.execute(stmt)
    db.commit()