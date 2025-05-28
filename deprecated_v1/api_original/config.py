"""Unified configuration for News Copilot API"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

# Load .env from parent directory if running from api/
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to default behavior

@dataclass
class Config:
    """Application configuration"""
    # Core API settings
    XAI_API_KEY: str = os.getenv('XAI_API_KEY', '')
    BASE_URL: str = os.getenv('BASE_URL', 'http://localhost:8080')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '8080'))
    
    # Supabase configuration
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY: str = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')
    
    # Feature flags
    AUTH_REQUIRED: bool = os.getenv('AUTH_REQUIRED', 'false').lower() == 'true'
    RATE_LIMITING: bool = os.getenv('RATE_LIMITING', 'true').lower() == 'true'
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # Analysis settings
    DEFAULT_TIMEOUT: int = 150  # seconds
    MAX_ARTICLE_LENGTH: int = 50000  # characters
    EXCLUDED_SITES_CONFIG_PATH: Optional[str] = os.getenv('EXCLUDED_SITES_CONFIG_PATH', 'config/low_quality_sites.yml')
    
    # Model selection
    JARGON_MODEL: str = 'grok-3-mini'
    VIEWPOINTS_MODEL: str = 'grok-3'
    DEEP_ANALYSIS_MODEL: str = 'grok-3'
    
    def validate(self):
        """Validate required configuration"""
        if not self.XAI_API_KEY:
            raise ValueError("XAI_API_KEY is required")
        
        if self.AUTH_REQUIRED and not all([
            self.SUPABASE_URL,
            self.SUPABASE_ANON_KEY,
            self.SUPABASE_SERVICE_KEY
        ]):
            raise ValueError("Supabase configuration required when AUTH_REQUIRED=true")

# Constants
COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Create global config instance
config = Config()

# Make EXCLUDED_SITES_CONFIG_PATH available at module level for direct import
EXCLUDED_SITES_CONFIG_PATH = config.EXCLUDED_SITES_CONFIG_PATH

# Validate on import (only in production)
if not os.getenv('DEBUG_MODE', 'false').lower() == 'true':
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        # Allow running without full config in development
        if os.getenv('NODE_ENV') == 'production':
            raise
else:
    print("⚠️  Running in DEBUG mode - skipping strict config validation")