# Router initialization
from fastapi import APIRouter

# Create the base router
api_router = APIRouter()

# Import routers - note: no * imports to avoid circular dependencies
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.courses import router as courses_router
from app.routers.blogs import router as blogs_router
from app.routers.cart import router as cart_router
from app.routers.wishlist import router as wishlist_router
from app.routers.payment import router as payment_router

# Register the routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(courses_router, prefix="/courses", tags=["Courses"])
api_router.include_router(payment_router, prefix="/payment", tags=["Payment"])
api_router.include_router(blogs_router, prefix="/blogs", tags=["Blogs"])
api_router.include_router(cart_router, prefix="/cart", tags=["Cart"])
api_router.include_router(wishlist_router, prefix="/wishlist", tags=["Wishlist"])