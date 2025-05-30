"""Base provider configuration and utilities"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from openai import OpenAI


@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    name: str
    base_url: str
    api_key_env: str
    models: List[str]
    capabilities: Dict[str, bool]
    default_model: str
    
    @property
    def api_key(self) -> str:
        """Get API key from environment"""
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"Missing API key environment variable: {self.api_key_env}")
        return key


PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
    "grok": ProviderConfig(
        name="grok",
        base_url="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
        models=["grok-3", "grok-3-mini", "grok-2-vision-1212"],
        capabilities={
            "web_search": True,
            "vision": True,
            "audio": False,
            "structured_output": True,
            "function_calling": True,
            "streaming": True
        },
        default_model="grok-3"
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        base_url="https://api.anthropic.com/v1/",
        api_key_env="ANTHROPIC_API_KEY",
        models=["claude-opus-4-20250514", "claude-3-5-sonnet-20241022"],
        capabilities={
            "web_search": False,
            "vision": True,
            "audio": False,
            "structured_output": True,
            "function_calling": True,
            "streaming": True,
            "extended_thinking": True
        },
        default_model="claude-opus-4-20250514"
    ),
    "gemini": ProviderConfig(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GEMINI_API_KEY",
        models=["gemini-2.0-flash", "gemini-2.5-flash-preview-05-20", "gemini-1.5-pro"],
        capabilities={
            "web_search": False,
            "vision": True,
            "audio": True,
            "structured_output": True,
            "function_calling": True,
            "streaming": True,
            "reasoning": True
        },
        default_model="gemini-2.0-flash"
    )
}


def create_client(provider: str, **kwargs) -> OpenAI:
    """Create an OpenAI-compatible client for the specified provider
    
    Args:
        provider: Provider name ('grok', 'anthropic', 'gemini')
        **kwargs: Additional arguments to pass to OpenAI client
        
    Returns:
        OpenAI client configured for the provider
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDER_CONFIGS.keys())}")
    
    config = PROVIDER_CONFIGS[provider]
    
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        **kwargs
    )


def get_provider_capabilities(provider: str) -> Dict[str, bool]:
    """Get capabilities of a specific provider
    
    Args:
        provider: Provider name
        
    Returns:
        Dictionary of capability flags
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")
    
    return PROVIDER_CONFIGS[provider].capabilities


def get_provider_models(provider: str) -> List[str]:
    """Get available models for a provider
    
    Args:
        provider: Provider name
        
    Returns:
        List of available model names
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")
    
    return PROVIDER_CONFIGS[provider].models


def get_default_model(provider: str) -> str:
    """Get default model for a provider
    
    Args:
        provider: Provider name
        
    Returns:
        Default model name
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")
    
    return PROVIDER_CONFIGS[provider].default_model