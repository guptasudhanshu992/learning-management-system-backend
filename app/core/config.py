from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
import secrets

# Load .env file if it exists
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Learning Management System API"
    API_V1_STR: str = "/api"
    VERSION: str = "1.0.0"
    
    # Base URL for frontend (for CORS)
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Backend URL (official production domain)
    BACKEND_URL: str = "https://api.priceactionrepository.com"
    
    # CORS allowed origins
    CORS_ORIGINS: List[str] = [
        # Development origins
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        # Production origins
        "https://priceactionrepository.com",
        "https://www.priceactionrepository.com",
        "https://app.priceactionrepository.com",
        "https://dashboard.priceactionrepository.com",
    ]
    
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Password policy
    MIN_PASSWORD_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # CSRF protection
    CSRF_SECRET_KEY: str = secrets.token_urlsafe(32)
    CSRF_COOKIE_SECURE: bool = False  # Set to True in production
    CSRF_COOKIE_SAMESITE: str = "lax"
    CSRF_METHODS: List[str] = ["POST", "PUT", "DELETE", "PATCH"]
    
    # Rate limiting
    RATE_LIMIT_PER_SECOND: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./lms.db"
    
    # External services
    STRIPE_SECRET_KEY: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global instance of settings
settings = Settings()