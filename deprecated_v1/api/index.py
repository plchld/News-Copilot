"""
Vercel Serverless Function Entry Point
This file is the entry point for all API routes when deployed to Vercel
"""

import sys
import os

# Add the project root directory to Python path
# __file__ is /path/to/News-Copilot/api/index.py
# SCRIPT_DIR is /path/to/News-Copilot/api
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT is /path/to/News-Copilot
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now that project root is in sys.path, we can use absolute imports starting from 'api'
from api.app import create_app

# Create the Flask app
app = create_app()

# For local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Loads .env from CWD (expected to be project root)
    
    port = int(os.getenv('FLASK_PORT', '8080'))
    debug = False # Force Flask debug mode off
    
    print(f"Starting News Copilot API on http://localhost:{port}")
    print(f"Debug mode: {debug}")
    print("Press CTRL+C to quit")
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)