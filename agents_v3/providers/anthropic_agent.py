"""Anthropic agent with cache control blocks and async support"""

import time
import uuid
import asyncio
import os
from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from ..conversation_logging import logger, MessageType, LogLevel
from ..utils.prompt_loader import prompt_loader
from ..utils.enhanced_prompt_loader import enhanced_prompt_loader


class AnthropicAgent(BaseAgent):
    """Anthropic agent with native SDK, cache control blocks, and async support"""
    
    def __init__(self, config: AgentConfig):
        """Initialize Anthropic agent
        
        Args:
            config: Agent configuration
        """
        super().__init__(config)
        
        # Set default model if not specified
        if not self.config.model:
            self.config.model = "claude-3-5-haiku-latest"
        
        # Cache management
        self.system_prompt_cached = False
        self.cache_ttl_minutes = 5 if self.config.cache_ttl == "5m" else 60
        
    def _convert_ttl_to_seconds(self, ttl_str: str) -> int:
        """Convert TTL string to seconds
        
        Args:
            ttl_str: TTL string like "5m" or "1h"
            
        Returns:
            TTL in seconds
        """
        if ttl_str == "5m":
            return 300  # 5 minutes
        elif ttl_str == "1h":
            return 3600  # 1 hour
        else:
            return 300  # Default to 5 minutes
        
    def _init_client(self):
        """Initialize Anthropic async client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": "extended-cache-ttl-2025-04-11"
            }
        )
        
        # Pricing information for cost calculation
        self.pricing = {
            "claude-3-5-sonnet-20241022": {
                "input": 0.003, "output": 0.015,
                "cache_write_5m": 0.00375, "cache_write_1h": 0.006,
                "cache_read": 0.0003
            },
            "claude-3-5-haiku-20241022": {
                "input": 0.0008, "output": 0.004,
                "cache_write_5m": 0.001, "cache_write_1h": 0.0016,
                "cache_read": 0.00008
            },
            "claude-3-opus-20240229": {
                "input": 0.015, "output": 0.075,
                "cache_write_5m": 0.01875, "cache_write_1h": 0.03,
                "cache_read": 0.0015
            },
            "claude-3-5-haiku-latest": {
                "input": 0.0008, "output": 0.004,
                "cache_write_5m": 0.001, "cache_write_1h": 0.0016,
                "cache_read": 0.00008
            }
        }
    
    async def start_conversation(self, conversation_type: str = "analysis") -> str:
        """Start a new conversation with cached system prompt
        
        Args:
            conversation_type: Type of conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = f"anthropic_{conversation_type}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Log conversation start
        logger.log_message(
            conversation_id=conversation_id,
            agent_name=self.config.name,
            provider="anthropic",
            message_type=MessageType.SYSTEM,
            content=f"Starting {conversation_type} conversation",
            level=LogLevel.INFO,
            metadata={
                "model": self.config.model,
                "cache_ttl": self.config.cache_ttl,
                "cache_enabled": self.config.cache_system_prompt
            }
        )
        
        # Initialize conversation state
        self.active_conversations[conversation_id] = {
            "messages": [],
            "stories_processed": 0,
            "cache_hits": 0,
            "last_activity": time.time(),
            "conversation_type": conversation_type,
            "system_prompt": self._build_cached_system_prompt()
        }
        
        # Send initial message to establish cache using centralized prompt
        initial_message = enhanced_prompt_loader.render_prompt(
            "conversation_initialization",
            {
                "conversation_type": conversation_type,
                "agent_role": self.config.role.value,
                "search_enabled": False,
                "search_line": ""
            }
        )
        
        response = await self._send_cached_message(
            conversation_id,
            initial_message,
            is_system_init=True
        )
        
        logger.log_message(
            conversation_id=conversation_id,
            agent_name=self.config.name,
            provider="anthropic",
            message_type=MessageType.SYSTEM,
            content="Conversation initialized with cached system prompt",
            level=LogLevel.INFO,
            metadata={
                "cache_hit": False,
                "cache_tokens_written": len(initial_message.split()) * 1.3  # Rough estimate
            }
        )
        
        return conversation_id
    
    def _build_cached_system_prompt(self) -> List[Dict[str, Any]]:
        """Build system prompt with cache control blocks"""
        
        # Load the base instructions from external file
        try:
            # Try to load role-specific prompt file
            role_prompt_name = f"{self.config.role.value}_agent"
            base_instructions = prompt_loader.load_prompt(role_prompt_name)
        except FileNotFoundError:
            # Fallback to the config instructions if role-specific file not found
            base_instructions = self.config.instructions
        
        # Main instructions with cache control
        main_instructions = {
            "type": "text",
            "text": base_instructions,
            "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
        }
        
        # Analysis framework with cache control using centralized prompt
        framework_content = enhanced_prompt_loader.render_prompt("analysis_framework")
        framework_instructions = {
            "type": "text",
            "text": framework_content,
            "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
        }
        
        return [main_instructions, framework_instructions]
    
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
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Format message with story context if provided
        if story_context:
            formatted_message = self._format_story_message(message, story_context)
        else:
            formatted_message = message
        
        return await self._send_cached_message(conversation_id, formatted_message, cache_message)
    
    async def _send_cached_message(
        self,
        conversation_id: str,
        message: str,
        cache_message: bool = True,
        is_system_init: bool = False
    ) -> AgentResponse:
        """Send message with cache control blocks for optimization"""
        
        conversation = self.active_conversations[conversation_id]
        start_time = time.time()
        
        try:
            # Build messages for API call
            messages = []
            
            # Add conversation history
            for msg in conversation["messages"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current message with cache control if enabled
            if cache_message and len(conversation["messages"]) > 0:
                # Cache the conversation history up to this point
                message_content = [
                    {
                        "type": "text",
                        "text": message,
                        "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
                    }
                ]
            else:
                message_content = message
            
            messages.append({
                "role": "user",
                "content": message_content
            })
            
            # Prepare API call parameters
            api_params = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "system": conversation["system_prompt"],
                "messages": messages
            }
            
            # Add beta header for 1-hour cache if needed
            if self.config.cache_ttl == "1h":
                api_params["extra_headers"] = {
                    "anthropic-beta": "extended-cache-ttl-2025-04-11"
                }
            
            # Make async API call
            response = await self.client.messages.create(**api_params)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response content
            response_content = ""
            if response.content and len(response.content) > 0:
                response_content = response.content[0].text
            
            # Calculate token usage
            tokens_used = self._extract_token_usage(response)
            cache_tokens_read = tokens_used.get("cache_read_input_tokens", 0)
            cache_tokens_written = tokens_used.get("cache_creation_input_tokens", 0)
            
            cache_hit = cache_tokens_read > 0
            
            # Update conversation state
            conversation["messages"].extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_content}
            ])
            conversation["last_activity"] = time.time()
            if cache_hit:
                conversation["cache_hits"] += 1
            
            # Log the interaction
            if not is_system_init:
                logger.log_message(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="anthropic",
                    message_type=MessageType.USER,
                    content=message[:200] + "..." if len(message) > 200 else message,
                    level=LogLevel.INFO
                )
            
            logger.log_message(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="anthropic",
                message_type=MessageType.ASSISTANT,
                content=response_content[:200] + "..." if len(response_content) > 200 else response_content,
                level=LogLevel.INFO,
                metadata={
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time_ms,
                    "cost_estimate": 0.0,
                    "cache_hit": cache_hit,
                    "cache_tokens_read": cache_tokens_read,
                    "cache_tokens_written": cache_tokens_written
                }
            )
            
            # Create standardized response
            return AgentResponse(
                content=response_content,
                provider="anthropic",
                model=self.config.model,
                conversation_id=conversation_id,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                cost_estimate=0.0,
                cache_hit=cache_hit,
                cache_tokens_read=cache_tokens_read,
                cache_tokens_written=cache_tokens_written,
                metadata={
                    "finish_reason": response.stop_reason,
                    "cache_enabled": cache_message,
                    "stop_sequence": response.stop_sequence
                }
            )
            
        except Exception as e:
            error_message = str(e)
            logger.log_message(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="anthropic",
                message_type=MessageType.ERROR,
                content=f"Error: {error_message}",
                level=LogLevel.ERROR,
                metadata={"message_preview": message[:100]}
            )
            
            return AgentResponse(
                content="",
                provider="anthropic",
                model=self.config.model,
                conversation_id=conversation_id,
                error=error_message
            )
    
    async def process_story_batch(
        self,
        conversation_id: str,
        stories: List[Dict[str, Any]]
    ) -> List[AgentResponse]:
        """Process multiple stories in conversation with cache benefits
        
        Args:
            conversation_id: Active conversation ID
            stories: Stories to analyze
            
        Returns:
            List of responses for each story
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations[conversation_id]
        results = []
        
        logger.log_message(
            conversation_id=conversation_id,
            agent_name=self.config.name,
            provider="anthropic",
            message_type=MessageType.SYSTEM,
            content=f"Processing batch of {len(stories)} stories",
            level=LogLevel.INFO,
            metadata={"story_count": len(stories), "batch_start": True}
        )
        
        for i, story in enumerate(stories):
            try:
                # Create story analysis prompt
                story_prompt = self._create_story_analysis_prompt(story, i + 1, len(stories))
                
                # Process story with conversation context and caching
                response = await self._send_cached_message(
                    conversation_id,
                    story_prompt,
                    cache_message=True  # Cache each story analysis for potential reuse
                )
                
                # Update story tracking
                conversation["stories_processed"] += 1
                
                # Log story completion
                logger.log_message(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="anthropic",
                    message_type=MessageType.SYSTEM,
                    content=f"Completed analysis of story {i+1}: {story.get('headline', 'Unknown')}",
                    level=LogLevel.INFO,
                    metadata={
                        "story_id": story.get("id", f"story_{i}"),
                        "headline": story.get("headline", "Unknown"),
                        "analysis_type": self.config.role.value,
                        "tokens_used": response.tokens_used or {},
                        "response_time_ms": response.response_time_ms or 0,
                        "cost_estimate": response.cost_estimate or 0.0,
                        "cache_hit": response.cache_hit
                    }
                )
                
                results.append(response)
                
            except Exception as e:
                # Handle individual story errors gracefully
                error_response = AgentResponse(
                    content="",
                    provider="anthropic",
                    model=self.config.model,
                    conversation_id=conversation_id,
                    error=str(e),
                    metadata={"story_id": story.get("id", f"story_{i}")}
                )
                results.append(error_response)
                
                logger.log_message(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="anthropic",
                    message_type=MessageType.ERROR,
                    content=f"Error processing story {i+1}: {str(e)}",
                    level=LogLevel.ERROR,
                    metadata={
                        "story_id": story.get("id", f"story_{i}"),
                        "headline": story.get("headline", "Unknown")
                    }
                )
        
        return results
    
    async def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """End conversation and return statistics
        
        Args:
            conversation_id: Conversation to end
            
        Returns:
            Conversation statistics with cache performance metrics
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations.pop(conversation_id)
        
        # Calculate basic statistics
        total_messages = len(conversation["messages"])
        cache_hits = conversation.get("cache_hits", 0) or 0
        cache_hit_ratio = cache_hits / max(total_messages, 1) if total_messages > 0 else 0
        last_activity = conversation.get("last_activity") or time.time()
        duration = time.time() - last_activity
        
        stats = {
            "conversation_id": conversation_id,
            "stories_processed": conversation["stories_processed"],
            "total_messages": total_messages,
            "cache_hits": cache_hits,
            "cache_hit_ratio": cache_hit_ratio,
            "duration_minutes": duration / 60,
            "provider": "anthropic",
            "model": self.config.model
        }
        
        # Log conversation end with cache performance
        logger.log_message(
            conversation_id=conversation_id,
            agent_name=self.config.name,
            provider="anthropic",
            message_type=MessageType.SYSTEM,
            content=f"Conversation ended. Stats: {stats}",
            level=LogLevel.INFO,
            metadata=stats
        )
        
        return stats
    
    async def _search_web_impl(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Anthropic doesn't have built-in search, so this is a placeholder
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            Empty list (search not supported)
        """
        logger.log_message(
            conversation_id="search",
            agent_name=self.config.name,
            provider="anthropic",
            message_type=MessageType.ERROR,
            content="Web search not supported by Anthropic agent. Use Gemini agent for search capabilities.",
            level=LogLevel.WARNING,
            metadata={"query": query}
        )
        return []
    
    def _format_story_message(self, base_message: str, story_context: Dict[str, Any]) -> str:
        """Format message with story context"""
        story_section = self._format_story_for_analysis(story_context)
        return f"{story_section}\n\n{base_message}"
    
    def _create_story_analysis_prompt(
        self,
        story: Dict[str, Any],
        story_num: int,
        total_stories: int
    ) -> str:
        """Create comprehensive story analysis prompt optimized for caching"""
        
        story_section = self._format_story_for_analysis(story)
        
        # Use centralized story analysis prompt
        prompt = enhanced_prompt_loader.render_prompt(
            "story_analysis",
            {
                "story_section": story_section,
                "story_num": story_num,
                "total_stories": total_stories,
                "agent_role": self.config.role.value
            }
        )
        
        return prompt
    
    def _extract_token_usage(self, response) -> Dict[str, int]:
        """Extract token usage from Anthropic response"""
        try:
            usage = response.usage
            return {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_creation_input_tokens": getattr(usage, 'cache_creation_input_tokens', 0),
                "cache_read_input_tokens": getattr(usage, 'cache_read_input_tokens', 0)
            }
        except Exception:
            # Fallback estimation
            return {
                "input_tokens": 1500,
                "output_tokens": 800,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            }