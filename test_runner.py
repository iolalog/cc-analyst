#!/usr/bin/env python3
"""
Test runner script for the analytics assistant.
This script provides an easy way to run tests with proper environment setup.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run tests with proper environment setup."""
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Change to project directory
    os.chdir(project_root)
    
    # Check if we're in a uv environment
    if not os.getenv('VIRTUAL_ENV') and not os.getenv('UV_ACTIVE'):
        print("⚠️  No virtual environment detected.")
        print("Please run: source $HOME/.local/bin/env")
        print("Then try again.")
        sys.exit(1)
    
    # Install dev dependencies if not already installed
    print("📦 Installing dev dependencies...")
    try:
        subprocess.run(["uv", "sync", "--group", "dev"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dev dependencies: {e}")
        print("Trying alternative installation method...")
        try:
            subprocess.run(["uv", "add", "--dev", "pytest", "pytest-cov", "pytest-mock", "ruff", "mypy", "types-requests"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dev dependencies. Please install manually:")
            print("uv add --dev pytest pytest-cov pytest-mock ruff mypy types-requests")
            sys.exit(1)
    
    # Parse command line arguments
    test_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Default test command
    if not test_args:
        test_args = ["tests/", "-v", "--cov=src", "--cov-report=term-missing", "--cov-report=html"]
    
    # Run tests
    print("🧪 Running tests...")
    try:
        subprocess.run(["uv", "run", "pytest"] + test_args, check=True)
        print("✅ Tests completed successfully!")
        
        # Show coverage report location
        coverage_html = project_root / "htmlcov" / "index.html"
        if coverage_html.exists():
            print(f"📊 Coverage report: {coverage_html}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code: {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()