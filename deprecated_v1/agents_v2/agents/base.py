"""Base agent class for News Copilot agents"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ..providers import MultiProviderAgent


@dataclass
class AgentConfig:
    """Configuration for a news agent"""
    name: str
    description: str
    category: str
    provider: str = "grok"
    model: Optional[str] = None
    temperature: float = 0.7
    
    
class BaseNewsAgent(MultiProviderAgent):
    """Base class for all news analysis agents"""
    
    def __init__(self, config: AgentConfig, instructions: str, tools: Optional[List[Dict[str, Any]]] = None):
        """Initialize a news agent
        
        Args:
            config: Agent configuration
            instructions: System instructions for the agent
            tools: Optional list of tools the agent can use
        """
        super().__init__(
            name=config.name,
            instructions=instructions,
            provider=config.provider,
            model=config.model,
            tools=tools,
            temperature=config.temperature
        )
        
        self.config = config
        self.category = config.category
        
    def format_output(self, raw_response: str) -> Dict[str, Any]:
        """Format the raw response into structured output
        
        Override this in subclasses for specific formatting
        """
        return {
            "agent": self.name,
            "category": self.category,
            "content": raw_response,
            "provider": self.provider,
            "model": self.model
        }