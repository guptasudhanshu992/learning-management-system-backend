#!/usr/bin/env python3
"""
Development server runner for the Learning Management System backend.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent))

def run_server():
    """Run the FastAPI development server"""
    try:
        import uvicorn
        
        print("Starting Learning Management System Backend...")
        print("Server will be available at: http://localhost:8000")
        print("API documentation will be available at: http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Run the server
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("Error: uvicorn is not installed.")
        print("Please install it with: pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()