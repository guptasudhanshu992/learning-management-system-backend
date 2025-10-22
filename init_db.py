#!/usr/bin/env python3
"""
Database initialization script for the Learning Management System.
Handles both development (SQLite) and production (PostgreSQL) environments.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent))

from app.db.database import engine, Base
from app.core.config import settings
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database tables"""
    try:
        logger.info(f"Initializing database with URL: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Test database connection
        with engine.connect() as conn:
            if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
                # PostgreSQL connection test
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
            else:
                # SQLite connection test
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                logger.info(f"Connected to SQLite: {version}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully!")
        return True
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument("--init", action="store_true", help="Initialize database tables")
    parser.add_argument("--drop", action="store_true", help="Drop all tables (use with caution!)")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    
    args = parser.parse_args()
    
    if args.reset:
        logger.info("Resetting database...")
        if drop_all_tables() and init_database():
            logger.info("Database reset completed successfully!")
        else:
            logger.error("Database reset failed!")
            sys.exit(1)
    elif args.drop:
        if drop_all_tables():
            logger.info("Database tables dropped successfully!")
        else:
            logger.error("Failed to drop database tables!")
            sys.exit(1)
    elif args.init:
        if init_database():
            logger.info("Database initialization completed successfully!")
        else:
            logger.error("Database initialization failed!")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python init_db.py --init     # Initialize database")
        print("  python init_db.py --drop     # Drop all tables")
        print("  python init_db.py --reset    # Reset database (drop + init)")