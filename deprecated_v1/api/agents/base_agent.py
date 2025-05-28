"""Base Agent Classes for News Copilot Agentic Architecture"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
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
    GROK_3 = "grok-3-latest"
    GROK_3_FAST = "grok-3-fast"


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
    
    def __init__(self, config: AgentConfig, grok_client: Any, 
                 prompt_builder: Any, 
                 schema_builder: Any):
        super().__init__(config, grok_client)
        self.prompt_builder = prompt_builder
        self.schema_builder = schema_builder
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute analysis with intelligent model selection"""
        start_time = self.log_execution_start(context)
        session_id = context.get('session_id', 'unknown')
        
        # Performance tracking
        phase_times = {}
        
        try:
            # Phase 1: Model Selection
            phase_start = datetime.now()
            model = self.select_model(context)
            phase_times['model_selection'] = int((datetime.now() - phase_start).total_seconds() * 1000)
            
            # Phase 2: Prompt Building
            phase_start = datetime.now()
            self.logger.debug(f"[PROMPT_BUILD] {session_id} - {self.config.name} | Building prompt and schema")
            prompt = self.prompt_builder(context)
            schema = self.schema_builder()
            phase_times['prompt_build'] = int((datetime.now() - phase_start).total_seconds() * 1000)
            
            # Phase 3: Search Parameters
            phase_start = datetime.now()
            search_params = self._build_search_params(context)
            phase_times['search_params'] = int((datetime.now() - phase_start).total_seconds() * 1000)
            
            if search_params:
                self.logger.debug(
                    f"[SEARCH_PARAMS] {session_id} - {self.config.name} | "
                    f"Search enabled with {len(search_params.get('sources', []))} sources"
                )
            
            # Log pre-API performance
            prep_time = sum(phase_times.values())
            self.logger.info(
                f"[PRE_API_TIMING] {session_id} - {self.config.name} | "
                f"Total prep: {prep_time}ms | "
                f"Breakdown: model={phase_times['model_selection']}ms, "
                f"prompt={phase_times['prompt_build']}ms, "
                f"search={phase_times['search_params']}ms"
            )
            
            # Phase 4: API Call
            api_start = datetime.now()
            response = await self._call_grok(
                prompt=prompt,
                schema=schema,
                model=model,
                search_params=search_params,
                context=context
            )
            phase_times['api_call'] = int((datetime.now() - api_start).total_seconds() * 1000)
            
            # Phase 5: Response Validation
            phase_start = datetime.now()
            result_data = response.get('data')
            tokens_used = response.get('tokens_used', 0)
            
            # Validate response content for debugging empty results
            validation_status = self._validate_response_content(result_data, session_id)
            phase_times['validation'] = int((datetime.now() - phase_start).total_seconds() * 1000)
            
            # Calculate total execution time
            total_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log detailed performance breakdown
            api_percentage = (phase_times['api_call']/total_time_ms*100) if total_time_ms > 0 else 0
            prep_percentage = (prep_time/total_time_ms*100) if total_time_ms > 0 else 0
            
            self.logger.info(
                f"[PERFORMANCE_BREAKDOWN] {session_id} - {self.config.name} | "
                f"Total: {total_time_ms}ms | "
                f"API: {phase_times['api_call']}ms ({api_percentage:.1f}%) | "
                f"Prep: {prep_time}ms ({prep_percentage:.1f}%) | "
                f"Validation: {phase_times['validation']}ms | "
                f"Tokens: {tokens_used} | "
                f"Response: {validation_status}"
            )
            
            result = AgentResult(
                success=True,
                data=result_data,
                model_used=model,
                tokens_used=tokens_used,
                execution_time_ms=total_time_ms,
                agent_name=self.config.name,
                api_calls_count=response.get('api_calls_count', 1),
                refinement_calls_count=response.get('refinement_calls_count', 0)
            )
            
            # Log execution completion
            self.log_execution_end(context, start_time, result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            total_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log performance even on failure
            prep_time = sum(phase_times.values()) if phase_times else 0
            self.logger.error(
                f"[PERFORMANCE_FAILURE] {session_id} - {self.config.name} | "
                f"Failed after {total_time_ms}ms | "
                f"Prep completed: {prep_time}ms | "
                f"Phases completed: {list(phase_times.keys())} | "
                f"Error: {error_msg}"
            )
            
            result = AgentResult(
                success=False,
                error=error_msg,
                execution_time_ms=total_time_ms,
                agent_name=self.config.name
            )
            
            # Log execution failure
            self.log_execution_end(context, start_time, result)
            
            return result
    
    def _validate_response_content(self, data: Dict[str, Any], session_id: str) -> str:
        """Validate response content and return status for debugging empty results"""
        if not data:
            self.logger.warning(
                f"[EMPTY_RESPONSE] {session_id} - {self.config.name} | "
                f"Response data is None or empty"
            )
            return "EMPTY_DATA"
        
        if not isinstance(data, dict):
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
        for key, value in data.items():
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
        for key, value in data.items():
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
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API with traditional JSON schema approach"""
        session_id = context.get('session_id', 'unknown')
        
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
                        from api.utils.prompt_utils import inject_runtime_search_context
                        full_prompt = inject_runtime_search_context(full_prompt, search_params)
                    
                    # Use system/user structure for markdown response
                    messages = [
                        {"role": "system", "content": full_prompt},
                        {"role": "user", "content": context.get('article_text', '')}
                    ]
                else:
                    # Standard prompt building
                    # Import prompt utilities for consistent formatting
                    from api.utils.prompt_utils import build_prompt, inject_runtime_search_context
                    
                    # Check if this is a markdown-based agent
                    agent_name = self.config.name.lower()
                    is_markdown_agent = any(x in agent_name for x in ['jargon', 'viewpoint', 'fact'])
                    
                    # If prompt doesn't already include system prefix and guardrails, add them
                    if "News-Copilot" not in prompt:
                        # For markdown agents, don't include JSON schema
                        if is_markdown_agent:
                            system_prompt = prompt  # Use prompt as-is for markdown
                        else:
                            # Rebuild prompt with proper structure including JSON schema
                            system_prompt = build_prompt(prompt, schema)
                        
                        if search_params:
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
            
            # Log raw response for debugging
            self.logger.info(
                f"[RAW_RESPONSE] {session_id} - {self.config.name} | "
                f"Response length: {len(result_data) if result_data else 0} | "
                f"First 500 chars: {result_data[:500] if result_data else 'EMPTY'}"
            )
            
            if isinstance(result_data, str):
                # Parse markdown response based on agent type
                try:
                    from api.utils.markdown_parser import parse_markdown_response
                    
                    # Determine analysis type from agent name
                    agent_name = self.config.name.lower()
                    analysis_type = None
                    
                    if 'jargon' in agent_name:
                        analysis_type = 'jargon'
                    elif 'viewpoint' in agent_name:
                        analysis_type = 'viewpoints'
                    elif 'fact' in agent_name:
                        analysis_type = 'fact-check'
                    elif 'bias' in agent_name:
                        analysis_type = 'bias'
                    elif 'timeline' in agent_name:
                        analysis_type = 'timeline'
                    elif 'expert' in agent_name:
                        analysis_type = 'expert'
                    elif 'pulse' in agent_name:
                        analysis_type = 'x-pulse'
                    
                    if analysis_type and analysis_type in ['fact-check', 'jargon', 'viewpoints']:
                        # For markdown-based agents, return markdown directly
                        self.logger.info(f"Returning markdown directly for {analysis_type}")
                        result_data = {"markdown_content": result_data}
                    else:
                        # For other types, try JSON parsing as fallback
                        self.logger.info(f"Attempting JSON parse for {self.config.name}")
                        try:
                            result_data = json.loads(result_data)
                        except json.JSONDecodeError:
                            # Try to extract JSON from markdown code blocks
                            import re
                            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_data, re.DOTALL)
                            if json_match:
                                try:
                                    result_data = json.loads(json_match.group(1))
                                except json.JSONDecodeError:
                                    result_data = self._create_fallback_response(result_data)
                            else:
                                # Try to find any JSON object
                                json_match = re.search(r'\{.*\}', result_data, re.DOTALL)
                                if json_match:
                                    try:
                                        result_data = json.loads(json_match.group())
                                    except json.JSONDecodeError:
                                        result_data = self._create_fallback_response(result_data)
                                else:
                                    result_data = self._create_fallback_response(result_data)
                    
                except ImportError:
                    self.logger.warning("Markdown parser not available, falling back to JSON parsing")
                    # Fallback to JSON parsing
                    try:
                        result_data = json.loads(result_data)
                    except json.JSONDecodeError:
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
                "terms": [
                    {
                        "term": "Σφάλμα Ανάλυσης",
                        "explanation": "Η απάντηση δεν μπόρεσε να αναλυθεί σωστά. Παρακαλώ δοκιμάστε ξανά.",
                        "context": raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
                    }
                ]
            }
        elif 'viewpoints' in agent_name:
            return {
                "topic_analysis": "Σφάλμα ανάλυσης",
                "alternative_perspectives": "Η απάντηση δεν μπόρεσε να αναλυθεί σωστά. Παρακαλώ δοκιμάστε ξανά.",
                "key_sources": []
            }
        elif 'fact' in agent_name:
            # Try to extract some meaningful data from the raw content
            self.logger.info(f"Attempting to parse fact-check content from raw response")
            
            # Basic structure that matches the schema
            fallback = {
                "claims": [
                    {
                        "claim": "Σφάλμα επεξεργασίας",
                        "evidence_assessment": "χωρίς επαρκή στοιχεία",
                        "context": "Η απάντηση του AI δεν μπόρεσε να αναλυθεί σωστά. Το σύστημα προσπάθησε να επαληθεύσει τους ισχυρισμούς αλλά η μορφή της απάντησης ήταν προβληματική.",
                        "complexity_note": f"Πρωτότυπη απάντηση: {raw_content[:300]}..." if len(raw_content) > 300 else raw_content,
                        "sources": []
                    }
                ],
                "source_quality": {
                    "primary_sources": 0,
                    "secondary_sources": 0,
                    "source_diversity": "άγνωστο"
                }
            }
            
            # Try to extract claims if possible from the raw content
            import re
            claims_match = re.findall(r'"claim":\s*"([^"]+)"', raw_content)
            if claims_match:
                self.logger.info(f"Found {len(claims_match)} claims in raw content")
                fallback["claims"] = []
                for claim_text in claims_match[:5]:  # Max 5 claims
                    fallback["claims"].append({
                        "claim": claim_text,
                        "evidence_assessment": "χωρίς επαρκή στοιχεία",
                        "context": "Δεν ήταν δυνατή η πλήρης ανάλυση λόγω σφάλματος μορφοποίησης.",
                        "sources": []
                    })
            
            return fallback
        else:
            # Generic fallback
            return {
                "content": raw_content,
                "error": "Response parsing failed",
                "message": "Η απάντηση του AI δεν μπόρεσε να μορφοποιηθεί σωστά. Παρακαλώ δοκιμάστε ξανά."
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