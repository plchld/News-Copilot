"""Grok API Configuration for News Aggregator"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

@dataclass
class GrokConfig:
    """Grok API configuration"""
    # Core API settings
    XAI_API_KEY: str = os.getenv('XAI_API_KEY', '')
    
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

# Constants
COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Create global config instance
config = GrokConfig()

# Make EXCLUDED_SITES_CONFIG_PATH available at module level for direct import
EXCLUDED_SITES_CONFIG_PATH = config.EXCLUDED_SITES_CONFIG_PATH