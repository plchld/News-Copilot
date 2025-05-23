# api/index.py
# Vercel entry point for the Flask app

import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explain_with_grok import app

# This is the entry point for Vercel
# The Flask app instance is imported from the main module