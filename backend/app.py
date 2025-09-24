"""
Resume Analyzer - Main Application Entry Point

This is the primary entry point for the Resume Analyzer application.
Use this file to start the server in development or production.

Usage:
    Development: python app.py
    Production:  python -m uvicorn app:application --host 0.0.0.0 --port 8000
"""

import os
import sys
import logging

# Add current directory to Python path to find resume_analyzer module
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from resume_analyzer.main import app

# Export the app for uvicorn or other ASGI servers
application = app


def main():
    """Main entry point with environment-specific configuration"""
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    print("🚀 Starting Resume Analyzer API...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")

    import uvicorn

    uvicorn.run(
        "app:application",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    main()
