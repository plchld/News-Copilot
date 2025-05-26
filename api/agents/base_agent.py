"""Base Agent Classes for News Copilot Agentic Architecture"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable, Type
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available Grok models (non-fast versions for cost efficiency)"""
    GROK_3_MINI = "grok-3-mini"
    GROK_3 = "grok-3-latest"
    GROK_3_FAST = "grok-3-fast"
    # Added from guide, assuming these are new or aliases
    GROK_3_MINI_FAST = "grok-3-mini-fast"


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
                break
        
        raise Exception(f"Agent {agent_name} failed after {max_retries} attempts: {str(last_exception)}")


class BaseAgent(ABC, AsyncCommunicationMixin):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig, grok_client: Any):
        self.config = config
        self.grok_client = grok_client
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute the agent's task"""
        pass
    
    def log_execution_start(self, context: Dict[str, Any]) -> datetime:
        """Log the start of agent execution"""
        session_id = context.get('session_id', 'unknown')
        start_time = datetime.now()
        
        self.logger.info(
            f"[EXECUTION_START] {session_id} - {self.config.name} | "
            f"Type: {self.config.description} | "
            f"Complexity: {self.config.complexity.name} | "
            f"Default model: {self.config.default_model.value} | "
            f"Started: {start_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
        
        return start_time
    
    def log_execution_end(self, context: Dict[str, Any], start_time: datetime, 
                         result: AgentResult) -> None:
        """Log the end of agent execution"""
        session_id = context.get('session_id', 'unknown')
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        status = "SUCCESS" if result.success else "FAILED"
        
        log_msg = (
            f"[EXECUTION_END] {session_id} - {self.config.name} | "
            f"Status: {status} | "
            f"Duration: {duration_ms}ms | "
            f"Model used: {result.model_used.value if result.model_used else 'unknown'} | "
            f"Tokens: {result.tokens_used or 0}"
        )
        
        if result.success and result.data:
            data_summary = {k: len(v) if isinstance(v, (list, str)) else type(v).__name__ 
                          for k, v in result.data.items()}
            log_msg += f" | Data: {data_summary}"
        
        if result.error:
            log_msg += f" | Error: {result.error}"
            
        if result.success:
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)
    
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
        session_id = context.get('session_id', 'unknown')
        original_model = self.config.default_model
        model = original_model
        upgrade_reasons = []
        
        # Check user tier (premium/admin get better models)
        user_tier = context.get('user_tier', 'free')
        if user_tier in ['premium', 'admin'] and model == ModelType.GROK_3_MINI:
            # Upgrade to grok-3 for premium users on complex tasks
            if self.config.complexity in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]:
                model = ModelType.GROK_3_FAST
                upgrade_reasons.append(f"user_tier={user_tier} + complexity={self.config.complexity.name}")
        
        # Check article length (very long articles need better models)
        article_text = context.get('article_text', '')
        word_count = len(article_text.split())
        if word_count > 5000 and model == ModelType.GROK_3_MINI:
            model = ModelType.GROK_3
            upgrade_reasons.append(f"long_article={word_count}_words")
        
        # Check for previous failures (retry with better model)
        retry_count = context.get('retry_count', 0)
        if retry_count > 1 and model == ModelType.GROK_3_MINI:
            model = ModelType.GROK_3
            upgrade_reasons.append(f"retry_escalation={retry_count}")
        
        # Log model selection decision
        if model != original_model:
            self.logger.info(
                f"[MODEL_SELECTION] {session_id} - {self.config.name} | "
                f"Upgraded: {original_model.value} → {model.value} | "
                f"Reasons: {', '.join(upgrade_reasons)}"
            )
        else:
            self.logger.debug(
                f"[MODEL_SELECTION] {session_id} - {self.config.name} | "
                f"Using default: {model.value} | "
                f"Context: tier={user_tier}, words={word_count}, retries={retry_count}"
            )
        
        return model
    
    def log_api_call(self, context: Dict[str, Any], model: ModelType, prompt_size: int, start_time: datetime) -> None:
        """Log details about an API call"""
        session_id = context.get('session_id', 'unknown')
        self.logger.info(
            f"[API_CALL] {session_id} - {self.config.name} | "
            f"Model: {model.value} | "
            f"Prompt size: {prompt_size} chars | "
            f"Started: {start_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
    
    def log_api_response(self, context: Dict[str, Any], model: ModelType, tokens_used: int, 
                        execution_time_ms: int, success: bool, error: Optional[str] = None) -> None:
        """Log details about an API response"""
        session_id = context.get('session_id', 'unknown')
        status = "SUCCESS" if success else "FAILED"
        
        log_msg = (
            f"[API_RESPONSE] {session_id} - {self.config.name} | "
            f"Status: {status} | "
            f"Model: {model.value} | "
            f"Time: {execution_time_ms}ms | "
            f"Tokens: {tokens_used}"
        )
        
        if error:
            log_msg += f" | Error: {error}"
            
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)
    
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

    def __init__(
        self,
        config: AgentConfig,
        grok_client: Any,
        prompt_builder: Callable,
        response_model: Optional[Type[BaseModel]] = None, # Added
        schema_builder: Optional[Callable] = None  # Modified for clarity from guide
    ):
        super().__init__(config, grok_client)
        self.prompt_builder = prompt_builder
        self.response_model = response_model # Added
        self.schema_builder = schema_builder

    def _get_system_prompt(self) -> str: # Added based on guide
        """Returns a generic system prompt. Can be overridden by subclasses."""
        # This is a placeholder. Actual system prompt content might be more specific.
        return "You are a helpful AI assistant. Please follow the user's instructions carefully."

    async def _call_grok_structured(
        self,
        prompt: str,
        model: ModelType,
        search_params: Optional[Dict] = None,
        context: Dict[str, Any] = None
    ) -> BaseModel:
        """Call Grok API with structured output"""
        
        # Check if model supports structured output
        structured_models = [
            ModelType.GROK_3,
            ModelType.GROK_3_FAST,
            ModelType.GROK_3_MINI,
            ModelType.GROK_3_MINI_FAST
        ]
        
        if model not in structured_models or not self.response_model:
            # Fallback to traditional JSON schema approach
            # Assuming _call_grok_legacy will be the renamed _call_grok
            legacy_result_dict = await self._call_grok_legacy(prompt, self.schema_builder(), model, search_params, context)
            # We need to return a BaseModel instance, but legacy returns a dict.
            # This part might need adjustment based on how legacy schema validation/parsing is handled
            # For now, if it falls back, it cannot directly return a Pydantic model unless schema_builder handles it.
            # This indicates a potential design consideration: structured calls expect Pydantic models, legacy calls return dicts.
            # The execute method will handle dicts from legacy calls.
            # However, this method's signature is BaseModel. This is problematic for fallback.
            # Let's assume for now that if fallback occurs, an error or a compatible dict is raised/returned and handled by caller.
            # Or, the guide implies _call_grok_legacy would be called by execute, not by _call_grok_structured.
            # Re-reading: "If not, fall back to a legacy method (e.g., _call_grok_legacy ...)" - this implies _call_grok_structured itself does the fallback.
            # This means _call_grok_legacy must return something that can be used to construct self.response_model, or this method's return type is wrong.
            # The guide's `execute` method shows `_call_grok_legacy` being called directly when `response_model` is None.
            # So, this fallback here is likely if the *model type* doesn't support structured, even if response_model is provided.
            # For now, let's raise an error if fallback is needed here, as the calling context in `execute` should prevent this.
            self.logger.warning(f"Model {model.value} or response_model not suitable for structured output. Fallback handling should occur in execute.")
            raise ValueError(f"Model {model.value} does not support structured output or no response_model provided to _call_grok_structured.")

        try:
            # Log the structured call (using existing logger as _log_phase is not defined here)
            self.logger.info(
                f"Calling Grok with structured output. Model: {model.value}, Response Model: {self.response_model.__name__}"
            )
            
            # Build messages
            messages = [
                {"role": "system", "content": self._get_system_prompt()}, # Added system prompt call
                {"role": "user", "content": prompt}
            ]
            
            # Make structured API call
            response = await self.grok_client.async_client.beta.chat.completions.parse(
                model=model.value,
                messages=messages,
                response_format=self.response_model,
                search_parameters=search_params, # search_params might be named search_parameters
                temperature=0.7 # Temperature from example
            )
            
            # Get parsed result
            parsed_result = response.choices[0].message.parsed
            
            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                self.tokens_used = response.usage.total_tokens # Assuming self.tokens_used is a class member for AgentResult
                self.log_api_response(context, model, self.tokens_used, 0, True) # execution_time_ms needs to be calculated
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"Grok structured API error: {str(e)}, Model: {model.value}")
            # self._log_phase("grok_structured_error", error=str(e), model=model.value) # _log_phase not defined
            raise

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute analysis with structured output support"""
        # Standard setup
        # self._prepare_execution(context) # _prepare_execution not in original, from guide
        exec_start_time = self.log_execution_start(context) # Renamed start_time to avoid conflict
        session_id = context.get('session_id', 'unknown')
        tokens_used = 0 # Initialize tokens_used
        api_calls_count = 0 # Initialize api_calls_count
        # Performance tracking (simplified from original)
        phase_times = {}
        
        try:
            # Phase 1: Model Selection
            phase_start = datetime.now()
            model = self.select_model(context) # self.selected_model in guide, using existing
            self.selected_model = model # Store for potential later use, as in guide
            phase_times['model_selection'] = int((datetime.now() - phase_start).total_seconds() * 1000)

            # Phase 2: Prompt Building
            phase_start = datetime.now()
            # prompt = self._build_prompt(context) # _build_prompt not in original, from guide
            prompt = self.prompt_builder(context) # Using existing prompt_builder
            phase_times['prompt_build'] = int((datetime.now() - phase_start).total_seconds() * 1000)

            # Phase 3: Search Parameters
            phase_start = datetime.now()
            # search_params = self._build_search_params(context) # Already exists
            search_params = self._build_search_params(context)
            phase_times['search_params'] = int((datetime.now() - phase_start).total_seconds() * 1000)

            if search_params:
                self.logger.debug(
                    f"[SEARCH_PARAMS] {session_id} - {self.config.name} | "
                    f"Search enabled with {len(search_params.get('sources', []))} sources"
                )
            
            prep_time = sum(phase_times.values())
            self.logger.info(
                f"[PRE_API_TIMING] {session_id} - {self.config.name} | Total prep: {prep_time}ms"
            )

            result_data = None
            api_start_time = datetime.now()

            if self.response_model:
                # Call Grok with structured output
                structured_result = await self._call_grok_structured(
                    prompt, self.selected_model, search_params, context
                )
                # Convert Pydantic model to dict
                result_data = structured_result.model_dump()
                tokens_used = getattr(self, 'tokens_used', 0) # From _call_grok_structured
                api_calls_count = 1 # Assuming one call for now
            else:
                # Legacy JSON approach
                if not self.schema_builder:
                    raise ValueError("Schema builder is required for non-structured responses.")
                legacy_response = await self._call_grok_legacy( # Renamed from _call_grok
                    prompt, self.schema_builder(), self.selected_model, search_params, context
                )
                result_data = legacy_response.get('data')
                tokens_used = legacy_response.get('tokens_used', 0)
                api_calls_count = legacy_response.get('api_calls_count', 1)
            
            phase_times['api_call'] = int((datetime.now() - api_start_time).total_seconds() * 1000)

            # Phase 5: Response Validation (Simplified)
            phase_start = datetime.now()
            validation_status = self._validate_response_content(result_data, session_id)
            phase_times['validation'] = int((datetime.now() - phase_start).total_seconds() * 1000)

            total_time_ms = int((datetime.now() - exec_start_time).total_seconds() * 1000)

            self.logger.info(
                f"[PERFORMANCE_BREAKDOWN] {session_id} - {self.config.name} | "
                f"Total: {total_time_ms}ms | API: {phase_times['api_call']}ms | Tokens: {tokens_used}"
            )
            
            # Create success result (adapted from guide)
            # result = self._create_success_result(result_data) 
            # _create_success_result not defined, creating AgentResult directly
            agent_result = AgentResult(
                success=True,
                data=result_data,
                model_used=self.selected_model,
                tokens_used=tokens_used,
                execution_time_ms=total_time_ms,
                agent_name=self.config.name,
                api_calls_count=api_calls_count, # Added
                refinement_calls_count=0 # Assuming no refinement in this flow yet
            )
            self.log_execution_end(context, exec_start_time, agent_result)
            return agent_result
            
        except Exception as e:
            # Create error result (adapted from guide)
            # result = self._create_error_result(str(e))
            # _create_error_result not defined, creating AgentResult directly
            error_msg = str(e)
            total_time_ms = int((datetime.now() - exec_start_time).total_seconds() * 1000)
            self.logger.error(
                 f"[EXECUTION_FAILURE] {session_id} - {self.config.name} | Error: {error_msg} | Total time: {total_time_ms}ms"
            )
            agent_result = AgentResult(
                success=False,
                error=error_msg,
                execution_time_ms=total_time_ms,
                agent_name=self.config.name
            )
            self.log_execution_end(context, exec_start_time, agent_result)
            return agent_result

    def _validate_response_content(self, data: Optional[Dict[str, Any]], session_id: str) -> str: # data can be None
        """Validate response content and return status for debugging empty results"""
        if not data:
            self.logger.warning(
                f"[EMPTY_RESPONSE] {session_id} - {self.config.name} | "
                f"Response data is None or empty"
            )
            return "EMPTY_DATA"
        
        if not isinstance(data, dict): # This check is important
            self.logger.warning(
                f"[INVALID_RESPONSE] {session_id} - {self.config.name} | "
                f"Response data is not a dict: {type(data)}"
            )
            return f"INVALID_TYPE_{type(data).__name__}"
        
        # Check for specific content based on agent type
        content_keys = list(data.keys())
        if not content_keys:
            self.logger.warning(
                f"[EMPTY_CONTENT] {session_id} - {self.config.name} | "
                f"Response dict is empty"
            )
            return "EMPTY_DICT"
        
        # Check if main content arrays/objects are empty
        empty_fields = []
        for key, value in data.items(): # Iterate through dict items
            if isinstance(value, list) and len(value) == 0:
                empty_fields.append(key)
            elif isinstance(value, str) and len(value.strip()) == 0:
                empty_fields.append(key)
        
        if empty_fields:
            self.logger.warning(
                f"[EMPTY_FIELDS] {session_id} - {self.config.name} | "
                f"Empty fields detected: {empty_fields} | "
                f"Non-empty fields: {[k for k in content_keys if k not in empty_fields]}"
            )
            return f"PARTIAL_EMPTY_{len(empty_fields)}_fields"
        
        # Log successful content validation
        content_summary = {}
        for key, value in data.items(): # Iterate through dict items
            if isinstance(value, list):
                content_summary[key] = f"{len(value)}_items"
            elif isinstance(value, str):
                content_summary[key] = f"{len(value)}_chars"
            else:
                content_summary[key] = type(value).__name__
        
        self.logger.debug(
            f"[CONTENT_VALID] {session_id} - {self.config.name} | "
            f"Response structure: {content_summary}"
        )
        
        return "VALID_CONTENT"

    async def _call_grok_legacy(self, prompt: str, schema: Dict, model: ModelType, # Renamed from _call_grok
                                 search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API with appropriate configuration (legacy JSON mode)"""
        try:
            # Check if we have conversation history (for refinements)
            conversation_history = context.get('conversation_history', [])
            
            # Track if this is a refinement call (for rate limiting purposes)
            is_refinement = bool(conversation_history)
            
            if conversation_history:
                # This is a refinement call - should NOT count against rate limits
                self.logger.info(f"Making refinement call for {self.config.name} (not counted for rate limits)")
                
                # Use chat completion with history
                messages = [
                    {"role": "system", "content": prompt}
                ]
                messages.extend(conversation_history)
                
                response = await self.grok_client.async_client.chat.completions.create(
                    model=model.value,
                    messages=messages
                    # Note: Grok doesn't support response_format, JSON formatting handled in prompt
                )
            else:
                # Standard completion
                # Check if agent has custom prompt building (like ViewpointsAgent)
                if hasattr(self, '_build_custom_prompt'):
                    # Use custom prompt that includes article text
                    full_prompt = self._build_custom_prompt(context)
                    
                    # Still need to inject search context for custom prompts
                    if search_params:
                        from ..prompt_utils import inject_runtime_search_context
                        full_prompt = inject_runtime_search_context(full_prompt, search_params)
                    
                    messages = [{"role": "user", "content": full_prompt}]
                else:
                    # Standard prompt building
                    # Import prompt utilities for consistent formatting
                    from ..prompt_utils import build_prompt, inject_runtime_search_context
                    
                    # If prompt doesn't already include system prefix and guardrails, add them
                    if "News-Copilot" not in prompt:
                        # Rebuild prompt with proper structure
                        system_prompt = build_prompt(prompt, schema)
                        system_prompt = inject_runtime_search_context(system_prompt, search_params)
                    else:
                        # Prompt already includes system components
                        system_prompt = prompt
                    
                    # Build messages for chat completion
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context.get('article_text', '')}
                    ]
                
                # Build request
                request_params = {
                    "model": model.value,
                    "messages": messages
                }
                
                # Note: Grok doesn't support response_format like OpenAI
                # We'll rely on prompt instructions for JSON formatting
                
                # Add search parameters if provided
                if search_params:
                    request_params["extra_body"] = {"search_parameters": search_params}
                
                response = await self.grok_client.async_client.chat.completions.create(**request_params)
            
            # Parse response
            result_data = response.choices[0].message.content
            if isinstance(result_data, str):
                try:
                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract JSON from the response
                    self.logger.warning(f"Failed to parse JSON response, attempting extraction")
                    
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', result_data, re.DOTALL)
                    if json_match:
                        try:
                            result_data = json.loads(json_match.group())
                            self.logger.info(f"Successfully extracted JSON from response")
                        except json.JSONDecodeError:
                            # Still can't parse, create a minimal valid response
                            self.logger.error(f"Could not extract valid JSON, creating fallback response")
                            result_data = self._create_fallback_response(result_data)
                    else:
                        # No JSON found, create fallback
                        self.logger.error(f"No JSON structure found in response, creating fallback")
                        result_data = self._create_fallback_response(result_data)
            
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
    
    def _create_fallback_response(self, raw_content: str) -> Dict[str, Any]:
        """Create a fallback response when JSON parsing fails"""
        # Create agent-specific fallback based on agent name
        agent_name = self.config.name.lower()
        
        if 'jargon' in agent_name:
            return {
                "simplified_terms": [
                    {
                        "term": "Technical content",
                        "explanation": "The response could not be properly parsed. Please try again.",
                        "context": raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
                    }
                ]
            }
        elif 'viewpoints' in agent_name:
            return {
                "perspectives": [
                    {
                        "stakeholder": "Analysis Error",
                        "viewpoint": "The response could not be properly parsed. Please try again.",
                        "reasoning": raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
                    }
                ]
            }
        else:
            # Generic fallback
            return {
                "content": raw_content,
                "error": "Response parsing failed",
                "message": "The AI response could not be properly formatted. Please try again."
            }


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