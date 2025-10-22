from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
import secrets
import os

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
    
    # Environment detection
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database settings - Environment specific
    # PostgreSQL settings for production (Neon)
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # SQLite settings for development
    SQLITE_DATABASE_PATH: str = "./lms.db"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Get the appropriate database URI based on environment
        """
        # If DATABASE_URL is provided (e.g., from Neon), use it directly
        if self.DATABASE_URL:
            return self.DATABASE_URL
            
        # Check if we're in production environment
        if self.ENVIRONMENT.lower() == "production":
            # Build PostgreSQL URI from individual components
            if all([self.POSTGRES_HOST, self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
                return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            else:
                # Fallback to SQLite if PostgreSQL config is incomplete
                print("Warning: PostgreSQL configuration incomplete, falling back to SQLite")
                return f"sqlite:///{self.SQLITE_DATABASE_PATH}"
        else:
            # Development environment - use SQLite
            return f"sqlite:///{self.SQLITE_DATABASE_PATH}"
    
    # External services
    STRIPE_SECRET_KEY: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global instance of settings
settings = Settings()