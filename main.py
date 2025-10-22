import time
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from typing import Callable
import uuid
import logging
from datetime import datetime

# Import router modules
from app.routers import users, courses, auth, blogs, cart, wishlist, payment

# Import database connection
from app.db.database import engine
from app.db import models

# Import security middleware and config
from app.core.middleware import setup_middleware, limiter
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create tables in the database
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for the Learning Management System",
    version=settings.VERSION,
    docs_url="/docs",  # Enable default docs
    redoc_url="/redoc",  # Enable default redoc
)

# Apply security middleware
setup_middleware(app)

# Configure request logging
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Log every request with a unique ID for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Get client info
    client_host = request.client.host if request.client else "unknown"
    
    # Log request details
    logger.info(f"Request [{request_id}]: {request.method} {request.url.path} from {client_host}")
    
    # Measure request processing time
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Log response details
        process_time = time.time() - start_time
        logger.info(f"Response [{request_id}]: Status {response.status_code}, took {process_time:.4f}s")
        
        # Add request ID to response header for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        # Log exception details
        process_time = time.time() - start_time
        logger.error(f"Error [{request_id}]: {str(e)}, took {process_time:.4f}s")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Request-ID": request_id}
        )

# Note: Using default FastAPI docs at /docs and /redoc
# Rate limiting is applied globally through middleware

# Include routers with API versioning
api_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["Users"])
app.include_router(courses.router, prefix=f"{api_prefix}/courses", tags=["Courses"])
app.include_router(blogs.router, prefix=f"{api_prefix}/blogs", tags=["Blogs"])
app.include_router(cart.router, prefix=f"{api_prefix}/cart", tags=["Cart"])
app.include_router(wishlist.router, prefix=f"{api_prefix}/wishlist", tags=["Wishlist"])
app.include_router(payment.router, prefix=f"{api_prefix}/payment", tags=["Payment"])

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}",
        "documentation": "/docs",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }