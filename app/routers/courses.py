from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from slugify import slugify
from sqlalchemy import func, desc

from app.db.database import get_db
from app.db import models
from app.schemas.course import (
    CourseCreate, CourseResponse, CourseUpdate,
    ChapterCreate, ChapterResponse, ChapterUpdate,
    LessonCreate, LessonResponse, LessonUpdate,
    CategoryCreate, CategoryResponse, CategoryUpdate,
    ReviewCreate, ReviewResponse, ReviewUpdate
)
from app.core.auth import get_current_active_user, get_instructor_or_admin_user, get_admin_user

# Create router
router = APIRouter()

# Course endpoints
@router.get("", response_model=List[CourseResponse])
def get_courses(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None),
    category_id: Optional[int] = None,
    level: Optional[str] = None,
    language: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    featured: Optional[bool] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all published courses with filters
    """
    query = db.query(models.Course).filter(models.Course.published == True)
    
    # Apply filters
    if search:
        query = query.filter(models.Course.title.ilike(f"%{search}%"))
        
    if category_id:
        query = query.join(models.Course.categories).filter(models.Category.id == category_id)
        
    if level:
        query = query.filter(models.Course.level == level)
        
    if language:
        query = query.filter(models.Course.language == language)
        
    if price_min is not None:
        query = query.filter(models.Course.price >= price_min)
        
    if price_max is not None:
        query = query.filter(models.Course.price <= price_max)
        
    if featured is not None:
        query = query.filter(models.Course.featured == featured)
    
    # Get courses with pagination
    courses = query.order_by(desc(models.Course.created_at)).offset(skip).limit(limit).all()
    
    # Format response with calculated fields
    result = []
    for course in courses:
        # Calculate average rating
        avg_rating = db.query(func.avg(models.Review.rating)).filter(
            models.Review.course_id == course.id
        ).scalar() or 0
        
        # Count enrolled students
        enrolled_students_count = db.query(func.count(models.Enrollment.id)).filter(
            models.Enrollment.course_id == course.id
        ).scalar()
        
        # Format categories
        categories = [
            {"id": cat.id, "name": cat.name, "slug": cat.slug} 
            for cat in course.categories
        ]
        
        # Create response object
        course_response = {
            **vars(course),
            "instructor_name": f"{course.instructor.first_name} {course.instructor.last_name}",
            "rating": round(avg_rating, 1),
            "enrolled_students": enrolled_students_count,
            "categories": categories
        }
        
        result.append(course_response)
    
    return result

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Create new course (instructor or admin only)
    """
    # Create slug from title
    slug = slugify(course.title)
    
    # Check if slug already exists
    db_course = db.query(models.Course).filter(models.Course.slug == slug).first()
    if db_course:
        # Add random suffix to make unique
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        slug = f"{slug}-{suffix}"
    
    # Create new course
    new_course = models.Course(
        title=course.title,
        slug=slug,
        description=course.description,
        price=course.price,
        discount_price=course.discount_price,
        thumbnail=course.thumbnail,
        trailer_video=course.trailer_video,
        level=course.level,
        language=course.language,
        duration_minutes=course.duration_minutes,
        instructor_id=current_user.id,
        published=False  # Default to unpublished
    )
    
    # Add to DB
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    # Add categories if provided
    if course.category_ids:
        categories = db.query(models.Category).filter(
            models.Category.id.in_(course.category_ids)
        ).all()
        
        new_course.categories.extend(categories)
        db.commit()
    
    # Format response
    return {
        **vars(new_course),
        "instructor_name": f"{current_user.first_name} {current_user.last_name}",
        "rating": 0,
        "enrolled_students": 0,
        "categories": [
            {"id": cat.id, "name": cat.name, "slug": cat.slug}
            for cat in new_course.categories
        ]
    }

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int = Path(..., title="The ID of the course to get"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get course by ID
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is published
    if not course.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or not published"
        )
    
    # Calculate average rating
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.course_id == course.id
    ).scalar() or 0
    
    # Count enrolled students
    enrolled_students_count = db.query(func.count(models.Enrollment.id)).filter(
        models.Enrollment.course_id == course.id
    ).scalar()
    
    # Format response
    return {
        **vars(course),
        "instructor_name": f"{course.instructor.first_name} {course.instructor.last_name}",
        "rating": round(avg_rating, 1),
        "enrolled_students": enrolled_students_count,
        "categories": [
            {"id": cat.id, "name": cat.name, "slug": cat.slug}
            for cat in course.categories
        ]
    }

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_update: CourseUpdate,
    course_id: int = Path(..., title="The ID of the course to update"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Update course (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this course"
        )
    
    # Update course fields
    update_data = course_update.dict(exclude_unset=True)
    
    # Handle slug if title changes
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])
    
    # Handle categories if provided
    category_ids = update_data.pop("category_ids", None)
    
    # Update other fields
    for field, value in update_data.items():
        setattr(course, field, value)
    
    # Update categories
    if category_ids is not None:
        # Clear existing categories
        course.categories = []
        
        # Add new categories
        categories = db.query(models.Category).filter(
            models.Category.id.in_(category_ids)
        ).all()
        
        course.categories.extend(categories)
    
    db.commit()
    db.refresh(course)
    
    # Calculate average rating
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.course_id == course.id
    ).scalar() or 0
    
    # Count enrolled students
    enrolled_students_count = db.query(func.count(models.Enrollment.id)).filter(
        models.Enrollment.course_id == course.id
    ).scalar()
    
    # Format response
    return {
        **vars(course),
        "instructor_name": f"{course.instructor.first_name} {course.instructor.last_name}",
        "rating": round(avg_rating, 1),
        "enrolled_students": enrolled_students_count,
        "categories": [
            {"id": cat.id, "name": cat.name, "slug": cat.slug}
            for cat in course.categories
        ]
    }

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int = Path(..., title="The ID of the course to delete"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> None:
    """
    Delete course (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this course"
        )
    
    # Delete course
    db.delete(course)
    db.commit()

# Chapter endpoints
@router.get("/{course_id}/chapters", response_model=List[ChapterResponse])
def get_chapters(
    course_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all chapters for a course
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get chapters
    chapters = db.query(models.Chapter).filter(
        models.Chapter.course_id == course_id
    ).order_by(models.Chapter.position).all()
    
    # Format response with lesson counts
    result = []
    for chapter in chapters:
        # Count lessons in chapter
        lessons_count = db.query(func.count(models.Lesson.id)).filter(
            models.Lesson.chapter_id == chapter.id
        ).scalar()
        
        # Create response object
        chapter_response = {
            **vars(chapter),
            "lessons_count": lessons_count
        }
        
        result.append(chapter_response)
    
    return result

@router.post("/{course_id}/chapters", response_model=ChapterResponse)
def create_chapter(
    chapter: ChapterCreate,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Create new chapter for a course (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add chapters to this course"
        )
    
    # Create new chapter
    new_chapter = models.Chapter(
        title=chapter.title,
        description=chapter.description,
        position=chapter.position,
        course_id=course_id
    )
    
    # Add to DB
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    
    return {
        **vars(new_chapter),
        "lessons_count": 0
    }

@router.put("/{course_id}/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_update: ChapterUpdate,
    course_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Update chapter (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update chapters in this course"
        )
    
    chapter = db.query(models.Chapter).filter(
        models.Chapter.id == chapter_id,
        models.Chapter.course_id == course_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Update chapter fields
    for field, value in chapter_update.dict(exclude_unset=True).items():
        setattr(chapter, field, value)
    
    db.commit()
    db.refresh(chapter)
    
    # Count lessons
    lessons_count = db.query(func.count(models.Lesson.id)).filter(
        models.Lesson.chapter_id == chapter.id
    ).scalar()
    
    return {
        **vars(chapter),
        "lessons_count": lessons_count
    }

@router.delete("/{course_id}/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(
    course_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> None:
    """
    Delete chapter (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete chapters in this course"
        )
    
    chapter = db.query(models.Chapter).filter(
        models.Chapter.id == chapter_id,
        models.Chapter.course_id == course_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Delete chapter
    db.delete(chapter)
    db.commit()

# Lesson endpoints
@router.get("/{course_id}/chapters/{chapter_id}/lessons", response_model=List[LessonResponse])
def get_lessons(
    course_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all lessons for a chapter
    """
    chapter = db.query(models.Chapter).filter(
        models.Chapter.id == chapter_id,
        models.Chapter.course_id == course_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Get lessons
    lessons = db.query(models.Lesson).filter(
        models.Lesson.chapter_id == chapter_id
    ).order_by(models.Lesson.position).all()
    
    return lessons

@router.post("/{course_id}/chapters/{chapter_id}/lessons", response_model=LessonResponse)
def create_lesson(
    lesson: LessonCreate,
    course_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Create new lesson for a chapter (instructor or admin only)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the instructor of the course or an admin
    if current_user.id != course.instructor_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add lessons to this course"
        )
    
    chapter = db.query(models.Chapter).filter(
        models.Chapter.id == chapter_id,
        models.Chapter.course_id == course_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Create new lesson
    new_lesson = models.Lesson(
        title=lesson.title,
        content_type=lesson.content_type,
        content=lesson.content,
        video_url=lesson.video_url,
        duration_minutes=lesson.duration_minutes,
        position=lesson.position,
        is_preview=lesson.is_preview,
        chapter_id=chapter_id
    )
    
    # Add to DB
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    
    return new_lesson

# Category endpoints
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all categories
    """
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    
    # Format response with course counts
    result = []
    for category in categories:
        # Count courses in category
        course_count = db.query(func.count(models.Course.id)).join(
            models.Course.categories
        ).filter(
            models.Category.id == category.id,
            models.Course.published == True
        ).scalar()
        
        # Create response object
        category_response = {
            **vars(category),
            "course_count": course_count
        }
        
        result.append(category_response)
    
    return result

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_admin_user)
) -> Any:
    """
    Create new category (admin only)
    """
    # Create slug from name
    slug = slugify(category.name)
    
    # Check if slug already exists
    db_category = db.query(models.Category).filter(models.Category.slug == slug).first()
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    # Create new category
    new_category = models.Category(
        name=category.name,
        slug=slug,
        description=category.description
    )
    
    # Add to DB
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return {
        **vars(new_category),
        "course_count": 0
    }

# Review endpoints
@router.get("/{course_id}/reviews", response_model=List[ReviewResponse])
def get_reviews(
    course_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all reviews for a course
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get reviews
    reviews = db.query(models.Review).filter(
        models.Review.course_id == course_id
    ).order_by(desc(models.Review.created_at)).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for review in reviews:
        # Get user info
        user = db.query(models.User).filter(models.User.id == review.user_id).first()
        user_name = f"{user.first_name} {user.last_name}" if user else "Unknown User"
        
        # Create response object
        review_response = {
            **vars(review),
            "user_name": user_name
        }
        
        result.append(review_response)
    
    return result

@router.post("/{course_id}/reviews", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Create new review for a course (authenticated user)
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is enrolled in the course
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.user_id == current_user.id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in the course to leave a review"
        )
    
    # Check if user has already reviewed this course
    existing_review = db.query(models.Review).filter(
        models.Review.course_id == course_id,
        models.Review.user_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this course"
        )
    
    # Create new review
    new_review = models.Review(
        rating=review.rating,
        comment=review.comment,
        user_id=current_user.id,
        course_id=course_id
    )
    
    # Add to DB
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return {
        **vars(new_review),
        "user_name": f"{current_user.first_name} {current_user.last_name}"
    }