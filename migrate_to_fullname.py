#!/usr/bin/env python3
"""
Migration script to convert User model from first_name/last_name to full_name.
This script handles the database schema migration for the LMS system.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent))

from app.db.database import engine
from app.core.config import settings
from sqlalchemy import text, inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_existing_schema():
    """Check if the database has the old or new schema"""
    try:
        inspector = inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        
        if 'users' not in tables:
            logger.info("Users table doesn't exist yet. No migration needed.")
            return None
            
        # Get columns for users table
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        has_first_name = 'first_name' in column_names
        has_last_name = 'last_name' in column_names
        has_full_name = 'full_name' in column_names
        
        logger.info(f"Current users table columns: {column_names}")
        
        if has_first_name and has_last_name and not has_full_name:
            return "old_schema"
        elif has_full_name and not has_first_name and not has_last_name:
            return "new_schema"
        elif has_first_name and has_last_name and has_full_name:
            return "mixed_schema"
        else:
            return "unknown_schema"
            
    except Exception as e:
        logger.error(f"Error checking schema: {e}")
        return None

def migrate_to_full_name():
    """Migrate from first_name/last_name to full_name"""
    try:
        schema_state = check_existing_schema()
        
        if schema_state is None:
            logger.error("Could not determine schema state")
            return False
            
        if schema_state == "new_schema":
            logger.info("Database already uses full_name schema. No migration needed.")
            return True
            
        if schema_state == "unknown_schema":
            logger.error("Unknown schema state. Cannot proceed with migration.")
            return False
            
        with engine.connect() as conn:
            if schema_state == "old_schema":
                logger.info("Migrating from old schema (first_name/last_name) to new schema (full_name)")
                
                # Add full_name column
                logger.info("Adding full_name column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
                
                # Migrate existing data
                logger.info("Migrating existing data...")
                conn.execute(text("""
                    UPDATE users 
                    SET full_name = COALESCE(first_name, '') || 
                                   CASE 
                                       WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN ' ' 
                                       ELSE '' 
                                   END || 
                                   COALESCE(last_name, '')
                    WHERE full_name IS NULL
                """))
                
                # Make full_name NOT NULL after data migration
                logger.info("Making full_name column NOT NULL...")
                if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
                    conn.execute(text("ALTER TABLE users ALTER COLUMN full_name SET NOT NULL"))
                else:
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                    logger.info("SQLite detected. Recreating table with new schema...")
                    
                    # Create backup table
                    conn.execute(text("""
                        CREATE TABLE users_backup AS 
                        SELECT id, email, full_name, hashed_password, role, is_active, created_at, updated_at 
                        FROM users
                    """))
                    
                    # Drop original table
                    conn.execute(text("DROP TABLE users"))
                    
                    # Recreate table with new schema
                    conn.execute(text("""
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email VARCHAR(254) NOT NULL UNIQUE,
                            full_name VARCHAR(100) NOT NULL,
                            hashed_password VARCHAR(255) NOT NULL,
                            role VARCHAR(20) NOT NULL DEFAULT 'user',
                            is_active BOOLEAN NOT NULL DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    
                    # Restore data
                    conn.execute(text("""
                        INSERT INTO users (id, email, full_name, hashed_password, role, is_active, created_at, updated_at)
                        SELECT id, email, full_name, hashed_password, role, is_active, created_at, updated_at
                        FROM users_backup
                    """))
                    
                    # Drop backup table
                    conn.execute(text("DROP TABLE users_backup"))
                
                # Drop old columns (only for PostgreSQL)
                if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
                    logger.info("Dropping old first_name and last_name columns...")
                    conn.execute(text("ALTER TABLE users DROP COLUMN first_name"))
                    conn.execute(text("ALTER TABLE users DROP COLUMN last_name"))
                
                conn.commit()
                
            elif schema_state == "mixed_schema":
                logger.info("Found mixed schema. Completing migration...")
                
                # Update any missing full_name values
                conn.execute(text("""
                    UPDATE users 
                    SET full_name = COALESCE(first_name, '') || 
                                   CASE 
                                       WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN ' ' 
                                       ELSE '' 
                                   END || 
                                   COALESCE(last_name, '')
                    WHERE full_name IS NULL OR full_name = ''
                """))
                
                # Drop old columns (only for PostgreSQL)
                if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
                    logger.info("Dropping old first_name and last_name columns...")
                    conn.execute(text("ALTER TABLE users DROP COLUMN first_name"))
                    conn.execute(text("ALTER TABLE users DROP COLUMN last_name"))
                
                conn.commit()
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        schema_state = check_existing_schema()
        
        if schema_state == "new_schema":
            with engine.connect() as conn:
                # Check if we have any data
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.fetchone()[0]
                
                # Check if full_name values are not empty
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE full_name IS NULL OR full_name = ''"))
                empty_names = result.fetchone()[0]
                
                logger.info(f"Migration verification:")
                logger.info(f"  - Total users: {user_count}")
                logger.info(f"  - Users with empty full_name: {empty_names}")
                
                if empty_names == 0:
                    logger.info("✅ Migration verification passed!")
                    return True
                else:
                    logger.warning("⚠️  Some users have empty full_name values")
                    return False
        else:
            logger.error(f"Migration verification failed. Schema state: {schema_state}")
            return False
            
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate User model to use full_name instead of first_name/last_name")
    parser.add_argument("--check", action="store_true", help="Check current schema state")
    parser.add_argument("--migrate", action="store_true", help="Run the migration")
    parser.add_argument("--verify", action="store_true", help="Verify migration was successful")
    
    args = parser.parse_args()
    
    if args.check:
        schema_state = check_existing_schema()
        logger.info(f"Current schema state: {schema_state}")
        
    elif args.migrate:
        logger.info("Starting migration from first_name/last_name to full_name...")
        if migrate_to_full_name():
            logger.info("Migration completed successfully!")
            if verify_migration():
                logger.info("Migration verification passed!")
            else:
                logger.warning("Migration verification failed!")
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    elif args.verify:
        if verify_migration():
            logger.info("Migration verification passed!")
        else:
            logger.error("Migration verification failed!")
            sys.exit(1)
            
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python migrate_to_fullname.py --check      # Check current schema")
        print("  python migrate_to_fullname.py --migrate    # Run migration")
        print("  python migrate_to_fullname.py --verify     # Verify migration")