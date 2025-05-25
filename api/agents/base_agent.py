"""Base Agent Classes for News Copilot Agentic Architecture"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available Grok models (non-fast versions for cost efficiency)"""
    GROK_3_MINI = "grok-3-mini"
    GROK_3 = "grok-3"


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


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig, grok_client: Any):
        self.config = config
        self.grok_client = grok_client
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute the agent's task"""
        pass
    
    def select_model(self, context: Dict[str, Any]) -> ModelType:
        """
        Dynamically select the appropriate model based on context
        
        Factors considered:
        - Article length
        - User tier
        - Language complexity
        - System load
        - Previous failures
        """
        # Default to configured model
        model = self.config.default_model
        
        # Check user tier (premium/admin get better models)
        user_tier = context.get('user_tier', 'free')
        if user_tier in ['premium', 'admin'] and model == ModelType.GROK_3_MINI:
            # Upgrade to grok-3 for premium users on complex tasks
            if self.config.complexity in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]:
                model = ModelType.GROK_3
                self.logger.info(f"Upgraded to {model.value} for {user_tier} user")
        
        # Check article length (very long articles need better models)
        article_text = context.get('article_text', '')
        word_count = len(article_text.split())
        if word_count > 5000 and model == ModelType.GROK_3_MINI:
            model = ModelType.GROK_3
            self.logger.info(f"Upgraded to {model.value} for long article ({word_count} words)")
        
        # Check for previous failures (retry with better model)
        retry_count = context.get('retry_count', 0)
        if retry_count > 1 and model == ModelType.GROK_3_MINI:
            model = ModelType.GROK_3
            self.logger.info(f"Upgraded to {model.value} after {retry_count} retries")
        
        return model
    
    def estimate_cost(self, model: ModelType, estimated_tokens: int) -> float:
        """Estimate the cost of running this agent"""
        # Rough cost estimates (adjust based on actual pricing)
        cost_per_1k_tokens = {
            ModelType.GROK_3_MINI: 0.01,
            ModelType.GROK_3: 0.025  # ~60% more expensive than mini
        }
        return (estimated_tokens / 1000) * cost_per_1k_tokens.get(model, 0.01)


class AnalysisAgent(BaseAgent):
    """Base class for standard analysis agents"""
    
    def __init__(self, config: AgentConfig, grok_client: Any, 
                 prompt_builder: Any, schema_builder: Any):
        super().__init__(config, grok_client)
        self.prompt_builder = prompt_builder
        self.schema_builder = schema_builder
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute analysis with intelligent model selection"""
        start_time = datetime.now()
        
        try:
            # Select appropriate model
            model = self.select_model(context)
            
            # Build prompt and schema
            prompt = self.prompt_builder(context)
            schema = self.schema_builder()
            
            # Add search parameters if needed
            search_params = self._build_search_params(context)
            
            # Log execution details
            self.logger.info(f"Executing {self.config.name} with model {model.value}")
            
            # Execute with Grok
            response = await self._call_grok(
                prompt=prompt,
                schema=schema,
                model=model,
                search_params=search_params,
                context=context
            )
            
            # Calculate execution time
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=response.get('data'),
                model_used=model,
                tokens_used=response.get('tokens_used'),
                execution_time_ms=execution_time_ms,
                agent_name=self.config.name
            )
            
        except Exception as e:
            self.logger.error(f"Error in {self.config.name}: {str(e)}")
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                agent_name=self.config.name
            )
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API with appropriate configuration"""
        try:
            # Check if we have conversation history (for refinements)
            conversation_history = context.get('conversation_history', [])
            
            if conversation_history:
                # Use chat completion with history
                messages = [
                    {"role": "system", "content": prompt}
                ]
                messages.extend(conversation_history)
                
                response = await self.grok_client.chat.completions.create(
                    model=model.value,
                    messages=messages,
                    response_format={"type": "json_object", "schema": schema} if schema else None
                )
            else:
                # Standard completion
                # Build messages for chat completion
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context.get('article_text', '')}
                ]
                
                # Build request
                request_params = {
                    "model": model.value,
                    "messages": messages
                }
                
                # Add response format if schema provided
                if schema:
                    request_params["response_format"] = {"type": "json_object"}
                
                # Add search parameters if provided
                if search_params:
                    request_params["search_parameters"] = search_params
                
                response = await self.grok_client.chat.completions.create(**request_params)
            
            # Parse response
            result_data = response.choices[0].message.content
            if isinstance(result_data, str):
                try:
                    result_data = json.loads(result_data)
                except:
                    pass
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {
                'data': result_data,
                'tokens_used': tokens_used
            }
            
        except Exception as e:
            self.logger.error(f"Grok API error: {str(e)}")
            raise
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters if needed for this agent"""
        # Override in subclasses that need search
        return None


class NestedAgent(BaseAgent):
    """Base class for agents that coordinate sub-agents"""
    
    def __init__(self, config: AgentConfig, grok_client: Any, sub_agents: List[BaseAgent]):
        super().__init__(config, grok_client)
        self.sub_agents = sub_agents
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute with sub-agent orchestration"""
        start_time = datetime.now()
        
        try:
            # Select model for coordination
            model = self.select_model(context)
            
            # Execute sub-agents (can be parallel or sequential)
            sub_results = await self._execute_sub_agents(context)
            
            # Aggregate results
            aggregated_data = self._aggregate_results(sub_results, context)
            
            # Post-process with main model if needed
            final_result = await self._post_process(aggregated_data, model, context)
            
            # Calculate total execution time and tokens
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            total_tokens = sum(r.tokens_used or 0 for r in sub_results)
            total_tokens += final_result.get('tokens_used', 0)
            
            return AgentResult(
                success=True,
                data=final_result.get('data'),
                model_used=model,
                tokens_used=total_tokens,
                execution_time_ms=execution_time_ms,
                agent_name=self.config.name
            )
            
        except Exception as e:
            self.logger.error(f"Error in nested agent {self.config.name}: {str(e)}")
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                agent_name=self.config.name
            )
    
    async def _execute_sub_agents(self, context: Dict[str, Any]) -> List[AgentResult]:
        """Execute sub-agents - can be overridden for custom orchestration"""
        # Default: execute all sub-agents in parallel
        tasks = [agent.execute(context) for agent in self.sub_agents]
        return await asyncio.gather(*tasks)
    
    @abstractmethod
    def _aggregate_results(self, results: List[AgentResult], context: Dict[str, Any]) -> Dict:
        """Aggregate results from sub-agents"""
        pass
    
    async def _post_process(self, aggregated_data: Dict, model: ModelType, 
                           context: Dict[str, Any]) -> Dict:
        """Optional post-processing with the main model"""
        # Default: no post-processing
        return {'data': aggregated_data, 'tokens_used': 0}