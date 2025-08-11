#!/usr/bin/env python3
"""Simple run script for Assignment Scraper development."""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✓ Required dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment is properly configured."""
    env_file = Path(".env")
    if not env_file.exists():
        print("✗ .env file not found")
        print("Please copy .env.example to .env and configure it")
        return False
    
    print("✓ Environment file found")
    return True

def start_database():
    """Start database services with Docker Compose."""
    try:
        print("Starting database services...")
        result = subprocess.run([
            "docker-compose", "up", "-d", "postgres", "redis"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Database services started")
            return True
        else:
            print(f"✗ Failed to start database services: {result.stderr}")
            return False
    except FileNotFoundError:
        print("✗ Docker Compose not found. Please install Docker and Docker Compose")
        return False

def run_migrations():
    """Run database migrations."""
    try:
        print("Running database migrations...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Database migrations completed")
            return True
        else:
            print(f"✗ Migration failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("✗ Alembic not found. Please install requirements.txt")
        return False

def start_application():
    """Start the FastAPI application."""
    print("Starting Assignment Scraper API...")
    print("🚀 Application will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([
            "uvicorn", "src.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")

def main():
    """Main function to run the application."""
    print("🕷️  Assignment Scraper - Starting Development Server")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Ask user if they want to start database services
    start_db = input("Start database services with Docker? (y/n): ").lower().strip()
    if start_db in ['y', 'yes']:
        if not start_database():
            sys.exit(1)
        
        # Run migrations
        run_migrations()
    
    # Start application
    start_application()

if __name__ == "__main__":
    main() 