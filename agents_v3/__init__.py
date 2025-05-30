"""
Agents V3: Category-Based News Intelligence System

A sophisticated multi-agent news intelligence system using native SDKs 
(Anthropic, Gemini) with structured outputs, robust error handling,
and conditional agent activation.
"""

# Version info
__version__ = "3.0.0"
__author__ = "News Copilot Team"

# Main exports for convenient imports
from .orchestration.category_orchestrator import CategoryOrchestrator

from .providers.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentResponse
)

from .conversation_logging.conversation_logger import (
    logger,
    ConversationLogger,
    MessageType,
    LogLevel
)

from .utils.prompt_loader import PromptLoader, prompt_loader
from .utils.enhanced_prompt_loader import enhanced_prompt_loader
from .utils.discovery_parser import DiscoveryParser, ParsedStory

# Communication exports
from .communication import message_bus

# Provider-specific exports
from .providers.anthropic_agent import AnthropicAgent
from .providers.gemini_agent import GeminiAgent

__all__ = [
    # Orchestration
    "CategoryOrchestrator",
    
    # Base classes
    "BaseAgent", 
    "AgentConfig",
    "AgentRole",
    "AgentResponse",
    
    # Logging
    "logger",
    "ConversationLogger",
    "MessageType",
    "LogLevel",
    
    # Utilities
    "PromptLoader",
    "prompt_loader",
    "enhanced_prompt_loader",
    "DiscoveryParser",
    "ParsedStory",
    
    # Communication
    "message_bus",
    
    # Providers
    "AnthropicAgent",
    "GeminiAgent"
]