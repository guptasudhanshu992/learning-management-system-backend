from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from typing import List, Optional, Dict, Any

# Course Schemas
class CourseBase(BaseModel):
    title: str
    description: str
    price: float
    discount_price: Optional[float] = None
    level: str
    language: str
    duration_minutes: int

class CourseCreate(CourseBase):
    thumbnail: Optional[str] = None
    trailer_video: Optional[str] = None
    category_ids: List[int] = []

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    thumbnail: Optional[str] = None
    trailer_video: Optional[str] = None
    level: Optional[str] = None
    language: Optional[str] = None
    duration_minutes: Optional[int] = None
    category_ids: Optional[List[int]] = None
    published: Optional[bool] = None

class CourseResponse(CourseBase):
    id: int
    slug: str
    thumbnail: Optional[str] = None
    trailer_video: Optional[str] = None
    instructor_id: int
    instructor_name: str
    featured: bool
    published: bool
    created_at: datetime
    updated_at: datetime
    categories: List[Dict[str, Any]] = []
    rating: Optional[float] = None
    enrolled_students: int = 0

    class Config:
        orm_mode = True

# Chapter Schemas
class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None
    position: int

class ChapterCreate(ChapterBase):
    pass

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None

class ChapterResponse(ChapterBase):
    id: int
    course_id: int
    lessons_count: int = 0

    class Config:
        orm_mode = True

# Lesson Schemas
class LessonBase(BaseModel):
    title: str
    content_type: str
    position: int
    is_preview: bool = False

class LessonCreate(LessonBase):
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    position: Optional[int] = None
    is_preview: Optional[bool] = None

class LessonResponse(LessonBase):
    id: int
    chapter_id: int
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None

    class Config:
        orm_mode = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    slug: str
    course_count: int = 0

    class Config:
        orm_mode = True

# Review Schemas
class ReviewBase(BaseModel):
    rating: float
    comment: Optional[str] = None

    @validator('rating')
    def rating_must_be_valid(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    user_name: str
    course_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Quiz Question Schemas
class QuizQuestionOption(BaseModel):
    id: int
    text: str

class QuizQuestionBase(BaseModel):
    question_text: str
    options: List[QuizQuestionOption]
    correct_option_id: int
    explanation: Optional[str] = None

class QuizQuestionCreate(QuizQuestionBase):
    pass

class QuizQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[QuizQuestionOption]] = None
    correct_option_id: Optional[int] = None
    explanation: Optional[str] = None

class QuizQuestionResponse(QuizQuestionBase):
    id: int
    lesson_id: int

    class Config:
        orm_mode = True

class QuizSubmission(BaseModel):
    question_id: int
    selected_option_id: int

class QuizResult(BaseModel):
    correct_answers: int
    total_questions: int
    percentage: float
    passing_score: bool
    questions: List[Dict[str, Any]]