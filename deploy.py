#!/usr/bin/env python3
"""
Production deployment script for the Learning Management System.
Handles database migrations and application startup for production environment.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a shell command and log the result"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {description}: {e}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        return False

def check_environment():
    """Check if we're in production environment"""
    env = os.getenv("ENVIRONMENT", "development")
    if env != "production":
        logger.warning(f"Current environment: {env}")
        logger.warning("This script is intended for production deployment")
        return False
    return True

def install_dependencies():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def run_migrations():
    """Run database migrations"""
    # Generate migration if needed
    run_command("alembic revision --autogenerate -m 'Auto migration'", "Generating migration")
    
    # Run migrations
    return run_command("alembic upgrade head", "Running database migrations")

def start_application():
    """Start the FastAPI application"""
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    workers = os.getenv("WORKERS", "1")
    
    command = f"uvicorn main:app --host {host} --port {port} --workers {workers}"
    return run_command(command, "Starting application")

def main():
    """Main deployment function"""
    logger.info("Starting production deployment...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        logger.error("Database migration failed")
        sys.exit(1)
    
    logger.info("Deployment completed successfully!")
    logger.info("Starting application...")
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()