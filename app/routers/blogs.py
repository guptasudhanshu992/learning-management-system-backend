from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from sqlalchemy import func, desc
from slugify import slugify

from app.db.database import get_db
from app.db import models
from app.schemas.blog import (
    BlogPostCreate, BlogPostResponse, BlogPostUpdate,
    CommentCreate, CommentResponse, CommentUpdate,
    TagResponse
)
from app.core.auth import get_current_active_user, get_instructor_or_admin_user

# Create router
router = APIRouter()

# Blog post endpoints
@router.get("", response_model=List[BlogPostResponse])
def get_blog_posts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all published blog posts with filters
    """
    query = db.query(models.BlogPost).filter(models.BlogPost.published == True)
    
    # Apply filters
    if search:
        query = query.filter(
            (models.BlogPost.title.ilike(f"%{search}%")) | 
            (models.BlogPost.content.ilike(f"%{search}%"))
        )
    
    if tag:
        query = query.join(models.BlogPost.tags).filter(models.Tag.name == tag)
    
    # Get posts with pagination
    posts = query.order_by(desc(models.BlogPost.created_at)).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for post in posts:
        # Get author info
        author_name = f"{post.author.first_name} {post.author.last_name}" if post.author else "Unknown"
        
        # Get tags
        tags = [tag.name for tag in post.tags]
        
        # Count comments
        comments_count = db.query(func.count(models.Comment.id)).filter(
            models.Comment.post_id == post.id
        ).scalar()
        
        # Create response object
        post_response = {
            **vars(post),
            "author_name": author_name,
            "tags": tags,
            "comments_count": comments_count
        }
        
        result.append(post_response)
    
    return result

@router.post("", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
def create_blog_post(
    post: BlogPostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_instructor_or_admin_user)
) -> Any:
    """
    Create new blog post (instructor or admin only)
    """
    # Create slug from title
    slug = slugify(post.title)
    
    # Check if slug already exists
    db_post = db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first()
    if db_post:
        # Add random suffix to make unique
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        slug = f"{slug}-{suffix}"
    
    # Create new post
    new_post = models.BlogPost(
        title=post.title,
        slug=slug,
        content=post.content,
        excerpt=post.excerpt,
        cover_image=post.cover_image,
        published=post.published,
        author_id=current_user.id
    )
    
    # Add to DB
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Add tags
    if post.tags:
        for tag_name in post.tags:
            # Check if tag exists
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name.lower()).first()
            
            if not tag:
                # Create new tag
                tag = models.Tag(name=tag_name.lower())
                db.add(tag)
                db.commit()
                db.refresh(tag)
            
            # Add tag to post
            new_post.tags.append(tag)
        
        db.commit()
        db.refresh(new_post)
    
    # Format response
    return {
        **vars(new_post),
        "author_name": f"{current_user.first_name} {current_user.last_name}",
        "tags": [tag.name for tag in new_post.tags],
        "comments_count": 0
    }

@router.get("/{post_id}", response_model=BlogPostResponse)
def get_blog_post(
    post_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get blog post by ID
    """
    post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )
    
    # Check if post is published
    if not post.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found or not published"
        )
    
    # Get author info
    author_name = f"{post.author.first_name} {post.author.last_name}" if post.author else "Unknown"
    
    # Get tags
    tags = [tag.name for tag in post.tags]
    
    # Count comments
    comments_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.post_id == post.id
    ).scalar()
    
    # Format response
    return {
        **vars(post),
        "author_name": author_name,
        "tags": tags,
        "comments_count": comments_count
    }

@router.put("/{post_id}", response_model=BlogPostResponse)
def update_blog_post(
    post_update: BlogPostUpdate,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Update blog post (author or admin only)
    """
    post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )
    
    # Check if user is the author of the post or an admin
    if current_user.id != post.author_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this blog post"
        )
    
    # Update blog post fields
    update_data = post_update.dict(exclude_unset=True)
    
    # Handle slug if title changes
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])
    
    # Handle tags if provided
    tags = update_data.pop("tags", None)
    
    # Update other fields
    for field, value in update_data.items():
        setattr(post, field, value)
    
    # Update tags
    if tags is not None:
        # Clear existing tags
        post.tags = []
        
        # Add new tags
        for tag_name in tags:
            # Check if tag exists
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name.lower()).first()
            
            if not tag:
                # Create new tag
                tag = models.Tag(name=tag_name.lower())
                db.add(tag)
                db.commit()
                db.refresh(tag)
            
            # Add tag to post
            post.tags.append(tag)
    
    db.commit()
    db.refresh(post)
    
    # Format response
    return {
        **vars(post),
        "author_name": f"{post.author.first_name} {post.author.last_name}",
        "tags": [tag.name for tag in post.tags],
        "comments_count": db.query(func.count(models.Comment.id)).filter(
            models.Comment.post_id == post.id
        ).scalar()
    }

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> None:
    """
    Delete blog post (author or admin only)
    """
    post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )
    
    # Check if user is the author of the post or an admin
    if current_user.id != post.author_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this blog post"
        )
    
    # Delete post
    db.delete(post)
    db.commit()

# Comment endpoints
@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(
    post_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all comments for a blog post
    """
    post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )
    
    # Get root comments (no parent_id)
    comments = db.query(models.Comment).filter(
        models.Comment.post_id == post_id,
        models.Comment.parent_id.is_(None)
    ).order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    
    # Format response with replies
    result = []
    for comment in comments:
        # Get user info
        user = db.query(models.User).filter(models.User.id == comment.user_id).first()
        user_name = f"{user.first_name} {user.last_name}" if user else "Unknown User"
        
        # Get replies
        replies = db.query(models.Comment).filter(
            models.Comment.parent_id == comment.id
        ).order_by(models.Comment.created_at).all()
        
        replies_formatted = []
        for reply in replies:
            reply_user = db.query(models.User).filter(models.User.id == reply.user_id).first()
            reply_user_name = f"{reply_user.first_name} {reply_user.last_name}" if reply_user else "Unknown User"
            
            replies_formatted.append({
                **vars(reply),
                "user_name": reply_user_name
            })
        
        # Create response object
        comment_response = {
            **vars(comment),
            "user_name": user_name,
            "replies": replies_formatted
        }
        
        result.append(comment_response)
    
    return result

@router.post("/{post_id}/comments", response_model=CommentResponse)
def create_comment(
    comment: CommentCreate,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Create new comment for a blog post (authenticated user)
    """
    post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )
    
    # If this is a reply, check if parent comment exists
    if comment.parent_id:
        parent_comment = db.query(models.Comment).filter(models.Comment.id == comment.parent_id).first()
        if not parent_comment or parent_comment.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
    
    # Create new comment
    new_comment = models.Comment(
        content=comment.content,
        post_id=post_id,
        user_id=current_user.id,
        parent_id=comment.parent_id
    )
    
    # Add to DB
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # Format response
    return {
        **vars(new_comment),
        "user_name": f"{current_user.first_name} {current_user.last_name}",
        "replies": []
    }

# Tag endpoints
@router.get("/tags", response_model=List[TagResponse])
def get_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all tags
    """
    tags = db.query(models.Tag).offset(skip).limit(limit).all()
    
    # Format response with post counts
    result = []
    for tag in tags:
        # Count published posts with this tag
        posts_count = db.query(func.count(models.BlogPost.id)).join(
            models.BlogPost.tags
        ).filter(
            models.Tag.id == tag.id,
            models.BlogPost.published == True
        ).scalar()
        
        # Create response object
        tag_response = {
            **vars(tag),
            "posts_count": posts_count
        }
        
        result.append(tag_response)
    
    return result