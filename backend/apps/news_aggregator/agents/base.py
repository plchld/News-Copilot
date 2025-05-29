"""Base Agent Classes for News Copilot Django Integration"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
import json

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available AI models"""
    # Grok Models
    GROK_3_MINI = "grok-3-mini"
    GROK_3 = "grok-3-latest"
    GROK_3_FAST = "grok-3-fast"
    
    # Claude Models  
    CLAUDE_OPUS_4 = "claude-opus-4-20250514"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    CLAUDE_SONNET_3_7 = "claude-3-7-sonnet-20250219"
    CLAUDE_SONNET_3_5 = "claude-3-5-sonnet-latest"
    CLAUDE_HAIKU_3_5 = "claude-3-5-haiku-latest"


class ComplexityLevel(Enum):
    """Task complexity levels"""
    SIMPLE = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    description: str
    default_model: ModelType
    complexity: ComplexityLevel
    supports_streaming: bool = True
    max_retries: int = 3
    timeout_seconds: int = 120


@dataclass
class AgentResult:
    """Result from an agent execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    model_used: Optional[ModelType] = None
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None
    agent_name: Optional[str] = None
    api_calls_count: Optional[int] = None
    refinement_calls_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'model_used': self.model_used.value if self.model_used else None,
            'tokens_used': self.tokens_used,
            'execution_time_ms': self.execution_time_ms,
            'agent_name': self.agent_name,
            'api_calls_count': self.api_calls_count,
            'refinement_calls_count': self.refinement_calls_count
        }


class AsyncCommunicationMixin:
    """Mixin for async communication utilities"""
    
    @staticmethod
    async def execute_with_timeout(coro, timeout_seconds: int, agent_name: str = "unknown"):
        """Execute a coroutine with timeout and proper error handling"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise Exception(f"Agent {agent_name} timed out after {timeout_seconds} seconds")
        except Exception as e:
            raise Exception(f"Agent {agent_name} failed: {str(e)}")
    
    @staticmethod
    async def execute_with_semaphore(semaphore: asyncio.Semaphore, coro, agent_name: str = "unknown"):
        """Execute a coroutine with semaphore control"""
        async with semaphore:
            return await coro
    
    @staticmethod
    async def gather_with_error_handling(*coros, return_exceptions: bool = True) -> List[Any]:
        """Enhanced asyncio.gather with better error handling"""
        try:
            results = await asyncio.gather(*coros, return_exceptions=return_exceptions)
            return results
        except Exception as e:
            # If gather itself fails, return exceptions for all coroutines
            return [e] * len(coros)
    
    @staticmethod
    async def execute_with_retry(coro_factory: Callable, max_retries: int = 3, 
                                backoff_factor: float = 2.0, agent_name: str = "unknown"):
        """Execute a coroutine factory with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                coro = coro_factory()
                return await coro
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        raise last_exception


class BaseAgent(ABC, AsyncCommunicationMixin):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._semaphore = asyncio.Semaphore(3)  # Limit concurrent API calls
        
    @abstractmethod
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article content and return results"""
        pass
    
    def get_model_for_retry(self, retry_count: int) -> ModelType:
        """Dynamic model selection based on retry count"""
        if retry_count == 0:
            return self.config.default_model
        elif retry_count == 1:
            # Try a more capable model on first retry
            if self.config.default_model == ModelType.GROK_3_MINI:
                return ModelType.GROK_3
            return self.config.default_model
        else:
            # Use the most capable model for final attempts
            return ModelType.GROK_3
    
    def get_cache_key(self, article_id: str) -> str:
        """Generate cache key for this agent and article"""
        return f"agent:{self.config.name}:article:{article_id}"
    
    def cache_result(self, article_id: str, result: AgentResult, timeout: int = 3600):
        """Cache the agent result"""
        cache_key = self.get_cache_key(article_id)
        cache.set(cache_key, result.to_dict(), timeout)
    
    def get_cached_result(self, article_id: str) -> Optional[AgentResult]:
        """Get cached result if available"""
        cache_key = self.get_cache_key(article_id)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return AgentResult(
                success=cached_data.get('success', False),
                data=cached_data.get('data'),
                error=cached_data.get('error'),
                model_used=ModelType(cached_data['model_used']) if cached_data.get('model_used') else None,
                tokens_used=cached_data.get('tokens_used'),
                execution_time_ms=cached_data.get('execution_time_ms'),
                agent_name=cached_data.get('agent_name'),
                api_calls_count=cached_data.get('api_calls_count'),
                refinement_calls_count=cached_data.get('refinement_calls_count')
            )
        
        return None
    
    async def execute_with_monitoring(self, article_content: str, **kwargs) -> AgentResult:
        """Execute agent with monitoring and caching"""
        start_time = datetime.now()
        article_id = kwargs.get('article_id')
        
        # Check cache if article_id provided
        if article_id:
            cached_result = self.get_cached_result(article_id)
            if cached_result:
                self.logger.info(f"Cache hit for article {article_id}")
                return cached_result
        
        try:
            # Execute the actual processing
            result = await self.execute_with_timeout(
                self.process(article_content, **kwargs),
                timeout_seconds=self.config.timeout_seconds,
                agent_name=self.config.name
            )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = int(execution_time)
            result.agent_name = self.config.name
            
            # Cache successful results
            if result.success and article_id:
                self.cache_result(article_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {self.config.name} failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=int(execution_time),
                agent_name=self.config.name
            )


class AnalysisAgent(BaseAgent):
    """Base class for analysis agents with structured output"""
    
    def __init__(self, config: AgentConfig, schema: Dict[str, Any]):
        super().__init__(config)
        self.schema = schema
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    @abstractmethod
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        pass
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Basic output validation against schema"""
        # TODO: Implement proper schema validation using pydantic
        return isinstance(output, dict) and len(output) > 0


class NestedAgent(BaseAgent):
    """Base class for agents that coordinate multiple sub-agents"""
    
    def __init__(self, config: AgentConfig, sub_agents: List[BaseAgent]):
        super().__init__(config)
        self.sub_agents = sub_agents
    
    async def process_with_sub_agents(self, article_content: str, **kwargs) -> List[AgentResult]:
        """Process article with all sub-agents in parallel"""
        tasks = []
        
        for agent in self.sub_agents:
            task = agent.execute_with_monitoring(article_content, **kwargs)
            tasks.append(task)
        
        results = await self.gather_with_error_handling(*tasks)
        
        return [r for r in results if isinstance(r, AgentResult)]