"""Base agent interface for native SDK implementations"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import uuid
import asyncio


class AgentRole(Enum):
    """Different agent roles in the system"""
    DISCOVERY = "discovery"           # Find and categorize stories
    PERSPECTIVE = "perspective"       # Analyze from specific viewpoint
    FACT_CHECK = "fact_check"        # Verify claims and sources
    SYNTHESIS = "synthesis"          # Combine multiple perspectives
    SOCIAL_PULSE = "social_pulse"    # Social media analysis


@dataclass
class AgentResponse:
    """Standardized response from any agent"""
    content: str
    provider: str
    model: str
    conversation_id: str
    
    # Token usage
    tokens_used: Optional[Dict[str, int]] = None
    
    # Performance metrics
    response_time_ms: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    # Caching information
    cache_hit: bool = False
    cache_tokens_read: int = 0
    cache_tokens_written: int = 0
    
    # Error handling
    error: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    role: AgentRole
    instructions: str
    
    # Provider settings
    provider: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    
    # Caching settings
    cache_system_prompt: bool = True
    cache_ttl: str = "5m"  # "5m", "1h", etc.
    
    # Batch processing
    batch_size: int = 10
    max_conversation_turns: int = 50
    
    # Search capabilities
    enable_search: bool = False
    search_provider: str = "google"
    search_threshold: float = 0.5  # For Gemini dynamic search (0.0-1.0, lower = more searches)


class BaseAgent(ABC):
    """Abstract base class for all native SDK agents"""
    
    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
        # Agent identification and communication
        self.agent_id = f"{config.name}_{str(uuid.uuid4())[:8]}"
        self.message_bus = None  # Will be set when registered with message bus
        self.collaboration_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Conversation isolation and request queueing
        self.isolated_conversations: Dict[str, str] = {}  # requesting_agent -> conversation_id
        self.request_queue = asyncio.Queue()
        self.processing_requests = False
        self.request_lock = asyncio.Lock()
        
        # Initialize provider-specific client
        self._init_client()
    
    @abstractmethod
    def _init_client(self):
        """Initialize the native SDK client"""
        pass
    
    @abstractmethod
    async def start_conversation(self, conversation_type: str = "analysis") -> str:
        """Start a new conversation
        
        Args:
            conversation_type: Type of conversation
            
        Returns:
            Conversation ID
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        conversation_id: str,
        message: str,
        story_context: Optional[Dict[str, Any]] = None,
        cache_message: bool = True
    ) -> AgentResponse:
        """Send a message in the conversation
        
        Args:
            conversation_id: Active conversation ID
            message: Message to send
            story_context: Optional story context for analysis
            cache_message: Whether to cache this message
            
        Returns:
            Agent response
        """
        pass
    
    @abstractmethod
    async def process_story_batch(
        self,
        conversation_id: str,
        stories: List[Dict[str, Any]]
    ) -> List[AgentResponse]:
        """Process multiple stories in a conversation
        
        Args:
            conversation_id: Active conversation ID
            stories: Stories to analyze
            
        Returns:
            List of responses for each story
        """
        pass
    
    @abstractmethod
    async def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """End a conversation and return statistics
        
        Args:
            conversation_id: Conversation to end
            
        Returns:
            Conversation statistics including costs and cache performance
        """
        pass
    
    async def search_web(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search the web for information
        
        Args:
            query: Search query
            **kwargs: Provider-specific search parameters
            
        Returns:
            List of search results
        """
        if not self.config.enable_search:
            raise ValueError(f"Search not enabled for agent {self.config.name}")
        
        return await self._search_web_impl(query, **kwargs)
    
    @abstractmethod
    async def _search_web_impl(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Provider-specific web search implementation"""
        pass
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get current conversation statistics
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Current statistics
        """
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        conv = self.active_conversations[conversation_id]
        return {
            "conversation_id": conversation_id,
            "messages": len(conv.get("messages", [])),
            "stories_processed": conv.get("stories_processed", 0),
            "total_cost": conv.get("total_cost", 0.0),
            "cache_hits": conv.get("cache_hits", 0),
            "last_activity": conv.get("last_activity", 0)
        }
    
    def _calculate_cost_estimate(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_tokens_read: int = 0,
        cache_tokens_written: int = 0
    ) -> float:
        """Calculate cost estimate based on provider pricing
        
        Args:
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            cache_tokens_read: Tokens read from cache
            cache_tokens_written: Tokens written to cache
            
        Returns:
            Estimated cost in USD
        """
        # Provider-specific pricing per 1K tokens
        pricing = {
            "anthropic": {
                "claude-3-5-sonnet": {"input": 0.003, "output": 0.015, "cache_write": 0.00375, "cache_read": 0.0003},
                "claude-3-5-haiku": {"input": 0.0008, "output": 0.004, "cache_write": 0.001, "cache_read": 0.00008}
            },
            "gemini": {
                "gemini-2.0-flash": {"input": 0.001, "output": 0.008, "cache_discount": 0.75},
                "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105, "cache_discount": 0.75}
            },
            "openai": {
                "gpt-4o": {"input": 0.0025, "output": 0.01},
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
            }
        }
        
        provider_pricing = pricing.get(self.config.provider, {})
        model_pricing = provider_pricing.get(self.config.model, {"input": 0.003, "output": 0.015})
        
        if self.config.provider == "anthropic":
            # Anthropic-specific cache pricing
            cost = (
                (input_tokens / 1000) * model_pricing.get("input", 0.003) +
                (output_tokens / 1000) * model_pricing.get("output", 0.015) +
                (cache_tokens_written / 1000) * model_pricing.get("cache_write", 0.00375) +
                (cache_tokens_read / 1000) * model_pricing.get("cache_read", 0.0003)
            )
        elif self.config.provider == "gemini":
            # Gemini cache discount model
            cache_discount = model_pricing.get("cache_discount", 0.75)
            cached_input_cost = (cache_tokens_read / 1000) * model_pricing.get("input", 0.001) * (1 - cache_discount)
            regular_input_cost = ((input_tokens - cache_tokens_read) / 1000) * model_pricing.get("input", 0.001)
            output_cost = (output_tokens / 1000) * model_pricing.get("output", 0.008)
            cost = cached_input_cost + regular_input_cost + output_cost
        else:
            # Standard pricing (OpenAI, etc.)
            cost = (
                (input_tokens / 1000) * model_pricing.get("input", 0.003) +
                (output_tokens / 1000) * model_pricing.get("output", 0.015)
            )
        
        return cost
    
    def _format_story_for_analysis(self, story: Dict[str, Any]) -> str:
        """Format a story for analysis prompt
        
        Args:
            story: Story data
            
        Returns:
            Formatted story prompt
        """
        headline = story.get("headline", "No headline")
        category = story.get("category", "general")
        why_important = story.get("why_important", "")
        key_facts = story.get("key_facts", [])
        source = story.get("source", "")
        
        prompt = f"""## Story: {headline}

**Category**: {category}
**Source**: {source}
**Why Important**: {why_important}

**Key Facts**:
{chr(10).join(f"- {fact}" for fact in key_facts) if key_facts else "- No key facts provided"}
"""
        
        return prompt
    
    # Inter-agent communication methods
    
    def set_message_bus(self, message_bus):
        """Set the message bus for inter-agent communication
        
        Args:
            message_bus: AgentMessageBus instance
        """
        self.message_bus = message_bus
        message_bus.register_agent(self.agent_id, self)
    
    async def request_analysis_from_agent(
        self,
        target_agent_id: str,
        analysis_type: str,
        story_data: Dict[str, Any],
        conversation_id: Optional[str] = None,
        timeout_seconds: int = 300
    ) -> Optional[Dict[str, Any]]:
        """Request analysis from another agent
        
        Args:
            target_agent_id: ID of the target agent
            analysis_type: Type of analysis requested
            story_data: Story data to analyze
            conversation_id: Optional conversation context
            timeout_seconds: Response timeout
            
        Returns:
            Analysis result or None if failed
        """
        if not self.message_bus:
            raise ValueError("Message bus not configured for this agent")
        
        return await self.message_bus.request_analysis(
            requester_id=self.agent_id,
            target_agent_id=target_agent_id,
            analysis_type=analysis_type,
            story_data=story_data,
            conversation_id=conversation_id,
            timeout_seconds=timeout_seconds
        )
    
    async def request_synthesis(
        self,
        synthesis_agent_id: str,
        story_data: Dict[str, Any],
        perspectives: Dict[str, Dict[str, Any]],
        conversation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Request synthesis from synthesis agent
        
        Args:
            synthesis_agent_id: ID of the synthesis agent
            story_data: Original story data
            perspectives: Dictionary of perspective analyses
            conversation_id: Optional conversation context
            
        Returns:
            Synthesis result or None if failed
        """
        return await self.request_analysis_from_agent(
            target_agent_id=synthesis_agent_id,
            analysis_type="synthesis",
            story_data={
                "story": story_data,
                "perspectives": perspectives
            },
            conversation_id=conversation_id
        )
    
    async def collaborate_on_story(
        self,
        participant_agent_ids: List[str],
        collaboration_type: str,
        story_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Start a collaboration session with other agents
        
        Args:
            participant_agent_ids: List of other agent IDs to collaborate with
            collaboration_type: Type of collaboration
            story_data: Story data for collaboration
            session_id: Optional session identifier
            
        Returns:
            Collaboration session ID
        """
        if not self.message_bus:
            raise ValueError("Message bus not configured for this agent")
        
        return await self.message_bus.start_collaboration(
            initiator_id=self.agent_id,
            participant_ids=participant_agent_ids,
            collaboration_type=collaboration_type,
            shared_data={"story": story_data},
            session_id=session_id
        )
    
    def register_message_handler(self, message_type, handler: Callable):
        """Register a handler for incoming messages
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if not self.message_bus:
            raise ValueError("Message bus not configured for this agent")
        
        self.message_bus.register_message_handler(
            self.agent_id,
            message_type,
            handler
        )
    
    async def handle_analysis_request(self, message) -> Dict[str, Any]:
        """Handle an analysis request from another agent
        
        Args:
            message: AgentMessage with the request
            
        Returns:
            Analysis result
        """
        # Queue the request to prevent concurrent access
        request_data = {
            "message": message,
            "response_future": asyncio.Future()
        }
        
        await self.request_queue.put(request_data)
        
        # Start processing queue if not already processing
        async with self.request_lock:
            if not self.processing_requests:
                self.processing_requests = True
                asyncio.create_task(self._process_request_queue())
        
        # Wait for our request to be processed
        return await request_data["response_future"]
    
    async def _process_request_queue(self):
        """Process queued requests sequentially"""
        self.processing_requests = True
        
        try:
            while not self.request_queue.empty():
                request_data = await self.request_queue.get()
                message = request_data["message"]
                response_future = request_data["response_future"]
                
                try:
                    result = await self._handle_single_request(message)
                    response_future.set_result(result)
                except Exception as e:
                    response_future.set_result({"error": str(e)})
                    
        finally:
            self.processing_requests = False
    
    async def _handle_single_request(self, message) -> Dict[str, Any]:
        """Handle a single request with conversation isolation"""
        analysis_type = message.content.get("analysis_type")
        story_data = message.content.get("story_data")
        requesting_agent = message.sender_id
        
        if not analysis_type or not story_data:
            return {"error": "Invalid analysis request"}
        
        try:
            # Get or create isolated conversation for this requesting agent
            conversation_id = await self._get_isolated_conversation(requesting_agent)
            
            # Create analysis prompt
            discovery_context = story_data.get('discovery_content', '')
            question = story_data.get('question', 'General analysis')
            
            prompt = f"""You are a specialized news analysis agent. Please analyze the following request from {requesting_agent}:

Request: {question}

Discovery Context:
{discovery_context if discovery_context else "No discovery context provided."}

IMPORTANT INSTRUCTIONS:
- Provide a direct, comprehensive analysis that specifically addresses the question
- DO NOT ask questions or request clarification
- DO NOT simply repeat the discovery content
- Apply your analytical expertise to provide insights, context, and perspective
- Focus on answering the specific question asked
- If the question asks about Greek context, provide Greek-specific analysis
- If the question asks about international context, provide global perspective analysis
- Use the discovery content as background information, but provide original analysis

Your role is to be an expert analyst, not a content repeater. Provide thoughtful, specific analysis that directly addresses {requesting_agent}'s question."""
            
            # Process the analysis in the isolated conversation
            response = await self.send_message(
                conversation_id,
                prompt,
                story_context=story_data if isinstance(story_data, dict) else None
            )
            
            return {
                "analysis_type": analysis_type,
                "result": response.content,
                "provider": response.provider,
                "model": response.model,
                "cost_estimate": response.cost_estimate,
                "tokens_used": response.tokens_used,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_isolated_conversation(self, requesting_agent: str) -> str:
        """Get or create an isolated conversation for a requesting agent"""
        if requesting_agent not in self.isolated_conversations:
            # Create a new isolated conversation for this agent
            conversation_id = await self.start_conversation(f"isolated_from_{requesting_agent}")
            self.isolated_conversations[requesting_agent] = conversation_id
            
            from ..conversation_logging.conversation_logger import logger, MessageType, LogLevel
            logger.log_message(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider=self.config.provider,
                message_type=MessageType.SYSTEM,
                content=f"Created isolated conversation for {requesting_agent}",
                level=LogLevel.INFO
            )
        
        return self.isolated_conversations[requesting_agent]
    
    async def handle_broadcast_message(self, message) -> Dict[str, Any]:
        """Handle a broadcast message from another agent
        
        Args:
            message: AgentMessage with the broadcast content
            
        Returns:
            Acknowledgment response
        """
        try:
            # Store broadcast content for future reference in conversations
            if not hasattr(self, '_broadcast_content'):
                self._broadcast_content = {}
            
            sender_id = message.sender_id
            content = message.content
            
            # Store the broadcast content by sender
            self._broadcast_content[sender_id] = content
            
            # Log that we received the broadcast
            from ..conversation_logging.conversation_logger import logger, MessageType, LogLevel
            logger.log_message(
                conversation_id=message.session_id or "broadcast",
                agent_name=self.config.name,
                provider=self.config.provider,
                message_type=MessageType.SYSTEM,
                content=f"Received broadcast from {sender_id}",
                level=LogLevel.INFO
            )
            
            return {
                "status": "received",
                "from": sender_id,
                "content_length": len(str(content))
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _create_synthesis_prompt(self, story: Dict[str, Any], perspectives: Dict[str, Dict[str, Any]]) -> str:
        """Create a synthesis prompt from story and perspectives
        
        Args:
            story: Original story data
            perspectives: Dictionary of perspective analyses
            
        Returns:
            Synthesis prompt
        """
        story_section = self._format_story_for_analysis(story)
        
        prompt = f"""{story_section}

## Available Perspectives for Synthesis:

"""
        
        for perspective_type, analysis in perspectives.items():
            content = analysis.get("result", analysis.get("content", "No analysis available"))
            prompt += f"""### {perspective_type.replace('_', ' ').title()}:
{content[:500]}...

"""
        
        prompt += """## Synthesis Task:
Create a comprehensive, balanced synthesis that:
1. Integrates all available perspectives
2. Highlights areas of agreement and disagreement
3. Provides clear attribution for different viewpoints
4. Maintains objectivity while acknowledging different approaches
5. Offers actionable insights for readers

Focus on creating a unified narrative that helps readers understand the complete picture from all angles."""
        
        return prompt