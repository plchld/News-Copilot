"""
Configuration for News Aggregator
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
XAI_API_KEY = os.getenv("XAI_API_KEY")

# API Configuration
GROK_API_BASE_URL = "https://api.x.ai/v1"
GROK_DEFAULT_MODEL = "grok-3"
GROK_MINI_MODEL = "grok-3-mini"

# Analysis Configuration
ANALYSIS_TIMEOUT = 150  # seconds
MAX_RETRIES = 3

# Export Configuration
EXPORT_DIR = "data/exports"
PROCESSED_DIR = "data/processed"
ENRICHED_DIR = "data/enriched"

# Database Configuration (for future use)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///news_aggregator.db")

# Web Interface Configuration
WEB_HOST = "0.0.0.0"
WEB_PORT = 5001
WEB_DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Agent Configuration
AGENT_CONFIG = {
    "jargon": {
        "model": GROK_MINI_MODEL,
        "timeout": 30
    },
    "viewpoints": {
        "model": GROK_DEFAULT_MODEL,
        "timeout": 60
    },
    "fact_check": {
        "model": GROK_DEFAULT_MODEL,
        "timeout": 60
    },
    "bias": {
        "model": GROK_DEFAULT_MODEL,
        "timeout": 45
    },
    "timeline": {
        "model": GROK_DEFAULT_MODEL,
        "timeout": 45
    },
    "expert": {
        "model": GROK_DEFAULT_MODEL,
        "timeout": 60
    }
}

# Ensure directories exist
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(ENRICHED_DIR, exist_ok=True)
os.makedirs("data/storage", exist_ok=True)