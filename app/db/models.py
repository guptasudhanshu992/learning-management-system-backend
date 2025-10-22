from datetime import datetime
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Text, 
    Float, DateTime, Table, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base

# Association table for course categories
course_category = Table(
    'course_category',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

# Association table for wishlist
wishlist = Table(
    'wishlist',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    profile_picture = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String, default="user")  # 'user', 'admin', 'instructor'
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    courses_enrolled = relationship("Enrollment", back_populates="student")
    courses_created = relationship("Course", back_populates="instructor")
    cart_items = relationship("CartItem", back_populates="user")
    orders = relationship("Order", back_populates="user")
    blog_posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

# Course model
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text)
    price = Column(Float)
    discount_price = Column(Float, nullable=True)
    thumbnail = Column(String, nullable=True)
    trailer_video = Column(String, nullable=True)
    level = Column(String)  # 'beginner', 'intermediate', 'advanced'
    language = Column(String)
    duration_minutes = Column(Integer)
    featured = Column(Boolean, default=False)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    instructor = relationship("User", back_populates="courses_created")
    chapters = relationship("Chapter", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")
    reviews = relationship("Review", back_populates="course")
    categories = relationship("Category", secondary=course_category, back_populates="courses")
    cart_items = relationship("CartItem", back_populates="course")

# Chapter model
class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    position = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter")

# Lesson model
class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content_type = Column(String)  # 'video', 'text', 'quiz'
    content = Column(Text, nullable=True)  # For text content
    video_url = Column(String, nullable=True)  # For video content
    duration_minutes = Column(Integer, nullable=True)  # For video content
    position = Column(Integer)
    is_preview = Column(Boolean, default=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chapter = relationship("Chapter", back_populates="lessons")
    progress = relationship("UserLessonProgress", back_populates="lesson")
    quiz_questions = relationship("QuizQuestion", back_populates="lesson")

# User lesson progress model
class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    completed = Column(Boolean, default=False)
    progress_percentage = Column(Float, default=0.0)
    last_accessed = Column(DateTime, nullable=True)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="progress")

# Quiz question model
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text)
    options = Column(JSON)  # Stored as JSON: [{id: 1, text: "Option 1"}, ...]
    correct_option_id = Column(Integer)
    explanation = Column(Text, nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz_questions")

# Category model
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    courses = relationship("Course", secondary=course_category, back_populates="categories")

# Enrollment model
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    certificate_issued = Column(Boolean, default=False)
    
    # Relationships
    student = relationship("User", back_populates="courses_enrolled")
    course = relationship("Course", back_populates="enrollments")

# Review model
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float)
    comment = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="reviews")

# Blog post model
class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    content = Column(Text)
    cover_image = Column(String, nullable=True)
    excerpt = Column(String, nullable=True)
    published = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="blog_posts")
    comments = relationship("Comment", back_populates="post")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")

# Tag model
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    
    # Relationships
    posts = relationship("BlogPost", secondary="post_tags", back_populates="tags")

# Post-Tag association table
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('blog_posts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

# Comment model
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("BlogPost", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref=ForeignKey("parent_id"))

# Cart item model
class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    course = relationship("Course", back_populates="cart_items")

# Order model
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    payment_status = Column(String)  # 'pending', 'completed', 'failed'
    payment_method = Column(String)  # 'stripe', 'razorpay', etc.
    payment_id = Column(String, nullable=True)  # Payment gateway reference ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

# Order item model
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    price = Column(Float)  # Price at the time of purchase
    
    # Relationships
    order = relationship("Order", back_populates="order_items")