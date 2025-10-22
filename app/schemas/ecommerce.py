from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

# Cart Schemas
class CartItemBase(BaseModel):
    course_id: int

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(CartItemBase):
    id: int
    user_id: int
    course_title: str
    course_price: float
    course_discount_price: Optional[float] = None
    course_thumbnail: Optional[str] = None
    added_at: datetime

    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_price: float
    total_items: int

# Wishlist Schemas
class WishlistItemBase(BaseModel):
    course_id: int

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItemResponse(WishlistItemBase):
    user_id: int
    course_title: str
    course_price: float
    course_discount_price: Optional[float] = None
    course_thumbnail: Optional[str] = None
    course_rating: Optional[float] = None

    class Config:
        orm_mode = True

class WishlistResponse(BaseModel):
    items: List[WishlistItemResponse]
    total_items: int

# Order Schemas
class OrderItemBase(BaseModel):
    course_id: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    course_title: str

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    total_amount: float
    payment_method: str

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderResponse(OrderBase):
    id: int
    user_id: int
    payment_status: str
    payment_id: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        orm_mode = True