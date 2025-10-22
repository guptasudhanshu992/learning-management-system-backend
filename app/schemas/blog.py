from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

# Blog Post Schemas
class BlogPostBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    cover_image: Optional[str] = None
    tags: List[str] = []
    published: bool = False

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None

class BlogPostResponse(BlogPostBase):
    id: int
    slug: str
    cover_image: Optional[str] = None
    published: bool
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    comments_count: int = 0

    class Config:
        orm_mode = True

# Tag Schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    posts_count: int = 0

    class Config:
        orm_mode = True

# Comment Schemas
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(CommentBase):
    id: int
    post_id: int
    user_id: int
    user_name: str
    parent_id: Optional[int] = None
    created_at: datetime
    replies: List[Dict[str, Any]] = []

    class Config:
        orm_mode = True