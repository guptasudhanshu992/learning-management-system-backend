from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password with minimum 8 characters")

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")

class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    role: str
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserAdminCreate(UserCreate):
    role: str = "user"
    is_active: bool = True

class UserAdminUpdate(UserUpdate):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

# Login Schema
class Login(BaseModel):
    email: EmailStr
    password: str

# Password Reset Schemas
class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)