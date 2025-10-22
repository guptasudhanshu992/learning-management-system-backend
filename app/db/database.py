from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from app.core.config import settings
import logging

# Configure logging for SQL statements
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.WARNING)  # Set to logging.DEBUG to see all SQL statements

# Get database URL from settings
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# Determine if we're using PostgreSQL or SQLite
is_postgresql = SQLALCHEMY_DATABASE_URL.startswith("postgresql://")
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite://")

# Create SQLAlchemy engine with appropriate settings
if is_postgresql:
    # PostgreSQL configuration for production (Neon)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Check connections before using them from the pool
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_size=10,        # Connection pool size
        max_overflow=20,     # Maximum overflow connections
        echo=False           # Set to True to see SQL statements
    )
elif is_sqlite:
    # SQLite configuration for development
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,  # Check connections before using them from the pool
        pool_recycle=3600,   # Recycle connections after 1 hour
        echo=False           # Set to True to see SQL statements
    )
else:
    raise ValueError(f"Unsupported database URL: {SQLALCHEMY_DATABASE_URL}")

# Enable SQLite foreign key constraints (only for SQLite)
if is_sqlite:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
            cursor.close()

# Create SessionLocal class with proper settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent detached instance errors
)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        # Rollback on exception
        db.rollback()
        raise
    finally:
        db.close()