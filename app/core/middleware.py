from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_SECOND}/second"])

# Initialize CsrfProtect without the decorator
# This will simplify our implementation
csrf_protect = CsrfProtect()

def setup_middleware(app: FastAPI):
    """
    Setup middleware for the FastAPI application
    """
    # Configure CSRF protection manually
    csrf_protect._secret = settings.CSRF_SECRET_KEY
    csrf_protect._cookie_secure = settings.CSRF_COOKIE_SECURE
    csrf_protect._cookie_samesite = settings.CSRF_COOKIE_SAMESITE
    
    # CORS middleware - More permissive for development
    cors_origins = settings.CORS_ORIGINS
    if settings.ENVIRONMENT.lower() == "development":
        # In development, allow all localhost origins
        cors_origins = ["*"]  # Allow all origins in development
    
    print(f"Setting up CORS with origins: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Session middleware for CSRF protection
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        same_site="lax",  # Prevents CSRF attacks
        https_only=settings.CSRF_COOKIE_SECURE,  # True in production
    )
    
    # GZip middleware for compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Trusted Host middleware
    if settings.CORS_ORIGINS:
        hosts = [origin.replace("http://", "").replace("https://", "") for origin in settings.CORS_ORIGINS]
        # Add common development hosts
        development_hosts = [
            "localhost", 
            "127.0.0.1", 
            "localhost:8000", 
            "127.0.0.1:8000",
            "0.0.0.0:8000"
        ]
        # Add production host
        production_hosts = [
            "api.priceactionrepository.com"
        ]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts + development_hosts + production_hosts)
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        # Log CORS information for debugging
        origin = request.headers.get("origin")
        if origin:
            print(f"Request from origin: {origin}")
            print(f"Allowed CORS origins: {cors_origins}")
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # More permissive CSP for Swagger UI to work properly
        if request.url.path in ["/docs", "/redoc"]:
            # Allow inline styles and scripts for API documentation
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net unpkg.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data: validator.swagger.io; "
                "connect-src 'self'"
            )
        else:
            # Stricter CSP for other endpoints
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    # CSRF protection exception handler
    @app.exception_handler(CsrfProtectError)
    def csrf_protect_exception_handler(request, exc):
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF token missing or invalid"}
        )
    
    return app