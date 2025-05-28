#!/usr/bin/env python3
"""Quick setup test to verify everything is configured correctly"""

import os
import sys
import subprocess

# Try to import colorama, fallback to plain text if not available
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLOR = True
except ImportError:
    # Fallback without colors
    class Fore:
        GREEN = RED = CYAN = ""
    class Style:
        RESET_ALL = ""
    HAS_COLOR = False

def check_requirement(name, check_func, error_msg):
    """Check a single requirement"""
    print(f"Checking {name}... ", end="")
    try:
        if check_func():
            print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗{Style.RESET_ALL}")
            print(f"  {error_msg}")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗{Style.RESET_ALL}")
        print(f"  Error: {e}")
        return False

def main():
    print(f"\n{Fore.CYAN}News Copilot Setup Verification{Style.RESET_ALL}")
    print("=" * 40)
    
    all_good = True
    
    # Check Python version
    all_good &= check_requirement(
        "Python version",
        lambda: sys.version_info >= (3, 8),
        "Python 3.8+ required"
    )
    
    # Check .env file
    all_good &= check_requirement(
        ".env file",
        lambda: os.path.exists('.env'),
        "Run 'make setup-env' to create .env file"
    )
    
    # Check API key
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        all_good &= check_requirement(
            "XAI_API_KEY",
            lambda: bool(os.getenv('XAI_API_KEY')),
            "Add your Grok API key to .env file"
        )
    
    # Check Node.js
    all_good &= check_requirement(
        "Node.js",
        lambda: subprocess.run(['node', '--version'], capture_output=True).returncode == 0,
        "Install Node.js 18+"
    )
    
    # Check web directory
    all_good &= check_requirement(
        "Web app structure",
        lambda: os.path.exists('web/package.json'),
        "Web app not found"
    )
    
    # Check API structure
    all_good &= check_requirement(
        "API structure",
        lambda: all(os.path.exists(p) for p in [
            'api/index.py',
            'api/app.py',
            'api/routes/__init__.py',
            'api/core/__init__.py'
        ]),
        "Run 'python migrate_api.py' to fix API structure"
    )
    
    # Check Python imports
    all_good &= check_requirement(
        "Python imports",
        lambda: test_imports(),
        "Missing Python dependencies - run 'pip install -r requirements.txt'"
    )
    
    print("\n" + "=" * 40)
    
    if all_good:
        print(f"{Fore.GREEN}✅ All checks passed!{Style.RESET_ALL}")
        print("\nYou can now run:")
        print("  make run      # Start both servers")
        print("  make test     # Run tests")
        print("\nOr use the quick start:")
        print("  python dev_server.py")
    else:
        print(f"{Fore.RED}❌ Some checks failed{Style.RESET_ALL}")
        print("\nPlease fix the issues above and try again.")
        print("See LOCAL_DEVELOPMENT.md for detailed instructions.")
        sys.exit(1)

def test_imports():
    """Test if required Python packages can be imported"""
    try:
        import flask
        import flask_cors
        import requests
        import trafilatura
        import openai
        import dotenv
        import pydantic
        import colorama
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    main()