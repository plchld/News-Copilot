"""
Configuration management for News Copilot API
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
MODEL = "grok-3"
API_URL = "https://api.x.ai/v1"
API_KEY = os.getenv("XAI_API_KEY")

# Flask Configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", "8080"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{FLASK_PORT}")

# Authentication Configuration
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# User Agent for web scraping
COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Rate limiting configuration
RATE_LIMITS = {
    'free': 10,
    'premium': 50,
    'admin': float('inf')
}