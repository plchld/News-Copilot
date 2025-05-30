"""Conversational agent with prompt caching optimization"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel

from ..providers.multi_provider_agent import MultiProviderAgent, AgentResponse
from ..tracing import trace_manager, SpanType


@dataclass
class ConversationConfig:
    """Configuration for conversational agents with caching"""
    
    # Agent configuration
    name: str
    instructions: str
    provider: str = "anthropic"  # Best for caching with 90% discount
    model: Optional[str] = None
    temperature: float = 0.7
    
    # Caching configuration
    cache_ttl: str = "5m"  # "5m" or "1h"
    max_conversation_length: int = 50  # Max turns before starting new conversation
    cache_system_prompt: bool = True
    cache_conversation_history: bool = True
    
    # Processing configuration
    batch_size: int = 10  # Stories to process in one conversation
    processing_timeout: int = 300  # 5 minutes


class ConversationState(BaseModel):
    """State of an ongoing conversation"""
    conversation_id: str
    messages: List[Dict[str, Any]]
    stories_processed: int
    last_activity: float
    cache_tokens_created: int = 0
    cache_tokens_read: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class ConversationalAgent:
    """Agent that maintains conversational context for batch processing with caching"""
    
    def __init__(self, config: ConversationConfig):
        """Initialize conversational agent
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        self.base_agent = MultiProviderAgent(
            name=config.name,
            instructions="", # Will be set dynamically
            provider=config.provider,
            model=config.model,
            temperature=config.temperature
        )
        
        # Conversation management
        self.active_conversations: Dict[str, ConversationState] = {}
        self.conversation_counter = 0
        
        # Build cached system prompt
        self.cached_system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> List[Dict[str, Any]]:
        """Build system prompt with cache control"""
        system_blocks = []
        
        # Main instructions (always cached)
        system_blocks.append({
            "type": "text",
            "text": self.config.instructions,
            "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
        })
        
        # Analysis framework (cached)
        framework_prompt = """
# Multi-Perspective Analysis Framework

For each story you analyze, provide a comprehensive analysis following this structure:

## Greek Perspective
- How Greek media is covering this story
- Unique Greek angles and concerns
- Political/economic implications for Greece
- Source diversity assessment

## International Perspective  
- How different regions frame the story
- Regional differences in coverage
- Global consensus vs divergences
- Cultural/political biases

## Alternative Views
- Contrarian or minority perspectives
- What mainstream media might miss
- Fact-checker disputes
- Reasonable skepticism

## Fact Verification
- Key claims verification status
- Primary sources found
- Confidence levels
- Areas of uncertainty

## Synthesis
- Unified narrative combining all perspectives
- Key agreements and disagreements
- Most important takeaways
- Greek relevance assessment

Maintain this structure for consistency and thorough analysis.
"""
        
        system_blocks.append({
            "type": "text", 
            "text": framework_prompt,
            "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
        })
        
        return system_blocks
    
    async def start_conversation(self, conversation_type: str = "analysis") -> str:
        """Start a new conversation session
        
        Args:
            conversation_type: Type of conversation (analysis, discovery, synthesis)
            
        Returns:
            Conversation ID
        """
        self.conversation_counter += 1
        conversation_id = f"{self.config.name}_{conversation_type}_{self.conversation_counter}_{int(time.time())}"
        
        # Initialize conversation state
        self.active_conversations[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            messages=[],
            stories_processed=0,
            last_activity=time.time()
        )
        
        with trace_manager.span(SpanType.CUSTOM, f"Start Conversation: {conversation_id}"):
            # Send initial message to establish cache
            initial_message = f"Starting {conversation_type} session. Ready to process stories in batch."
            
            await self._send_message(
                conversation_id,
                "user",
                initial_message,
                cache_conversation=False  # Don't cache the initial setup
            )
        
        return conversation_id
    
    async def process_story_batch(
        self,
        conversation_id: str,
        stories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process a batch of stories in the conversation
        
        Args:
            conversation_id: Active conversation ID
            stories: List of stories to analyze
            
        Returns:
            List of analysis results
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations[conversation_id]
        results = []
        
        with trace_manager.span(
            SpanType.CUSTOM, 
            f"Process Batch: {len(stories)} stories",
            conversation_id=conversation_id,
            batch_size=len(stories)
        ):
            
            for i, story in enumerate(stories):
                try:
                    # Create story analysis prompt
                    story_prompt = self._format_story_prompt(story, i + 1, len(stories))
                    
                    # Process with caching
                    response = await self._send_message(
                        conversation_id,
                        "user",
                        story_prompt,
                        cache_conversation=True  # Cache the growing conversation
                    )
                    
                    # Parse and store result
                    analysis_result = self._parse_analysis_response(story, response)
                    results.append(analysis_result)
                    
                    conversation.stories_processed += 1
                    
                except Exception as e:
                    # Handle individual story errors gracefully
                    error_result = {
                        "story_id": story.get("id", f"story_{i}"),
                        "headline": story.get("headline", "Unknown"),
                        "error": str(e),
                        "analysis": None
                    }
                    results.append(error_result)
        
        return results
    
    async def _send_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        cache_conversation: bool = True
    ) -> str:
        """Send a message in the conversation with caching
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant)
            content: Message content  
            cache_conversation: Whether to cache the conversation history
            
        Returns:
            Assistant response content
        """
        conversation = self.active_conversations[conversation_id]
        
        # Add user message to conversation
        if role == "user":
            conversation.messages.append({
                "role": "user",
                "content": content
            })
        
        # Prepare full message history with caching
        messages_for_api = []
        
        # Add system prompt (always cached)
        system_messages = self.cached_system_prompt
        
        # Add conversation history
        for msg in conversation.messages:
            messages_for_api.append(msg)
        
        # Mark the last message for caching if enabled
        if cache_conversation and messages_for_api:
            # Apply cache control to the last user message
            last_message = messages_for_api[-1]
            if isinstance(last_message["content"], str):
                last_message["content"] = [{
                    "type": "text",
                    "text": last_message["content"],
                    "cache_control": {"type": "ephemeral", "ttl": self.config.cache_ttl}
                }]
        
        # Make API call with caching
        with trace_manager.span(
            SpanType.GENERATION,
            f"Cached Generation: {self.config.provider}",
            conversation_id=conversation_id,
            cache_enabled=True
        ):
            
            # Create the API request with system and messages
            if self.config.provider == "anthropic":
                # Anthropic format with system separate
                response = await self._call_anthropic_with_cache(
                    system_messages,
                    messages_for_api
                )
            else:
                # OpenAI format with system in messages
                all_messages = [{"role": "system", "content": system_messages}] + messages_for_api
                response = await self.base_agent.run(all_messages)
        
        # Add assistant response to conversation
        conversation.messages.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Update conversation stats
        conversation.last_activity = time.time()
        if response.usage:
            conversation.total_input_tokens += response.usage.get("prompt_tokens", 0)
            conversation.total_output_tokens += response.usage.get("completion_tokens", 0)
            conversation.cache_tokens_read += response.usage.get("cache_read_input_tokens", 0)
            conversation.cache_tokens_created += response.usage.get("cache_creation_input_tokens", 0)
        
        return response.content
    
    async def _call_anthropic_with_cache(
        self,
        system_messages: List[Dict[str, Any]],
        conversation_messages: List[Dict[str, Any]]
    ) -> AgentResponse:
        """Call Anthropic API with proper caching structure"""
        
        # Build the request parameters
        params = {
            "model": self.base_agent.model,
            "max_tokens": 4000,
            "temperature": self.base_agent.temperature,
            "system": system_messages,
            "messages": conversation_messages
        }
        
        # For 1-hour cache, add beta header
        if self.config.cache_ttl == "1h":
            params["extra_headers"] = {
                "anthropic-beta": "extended-cache-ttl-2025-04-11"
            }
        
        # Call the API
        response = await self.base_agent._call_api(params)
        
        # Return standardized response
        return AgentResponse(
            content=response.choices[0].message.content,
            provider=self.base_agent.provider,
            model=self.base_agent.model,
            usage=response.usage.model_dump() if response.usage else None,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "cached": True
            }
        )
    
    def _format_story_prompt(self, story: Dict[str, Any], story_num: int, total_stories: int) -> str:
        """Format a story for analysis prompt"""
        
        headline = story.get("headline", "No headline")
        why_important = story.get("why_important", "")
        key_facts = story.get("key_facts", [])
        category = story.get("category", "general")
        
        prompt = f"""
## Story {story_num}/{total_stories}: {headline}

**Category:** {category}
**Why Important:** {why_important}

**Key Facts:**
{chr(10).join(f"- {fact}" for fact in key_facts)}

Please provide a comprehensive multi-perspective analysis of this story following the established framework. Focus on:
1. Greek media perspective and unique angles
2. International coverage differences
3. Alternative viewpoints and fact verification
4. Synthesized narrative with clear attribution

Be thorough but concise in your analysis.
"""
        
        return prompt
    
    def _parse_analysis_response(self, story: Dict[str, Any], response_content: str) -> Dict[str, Any]:
        """Parse the analysis response into structured format"""
        
        return {
            "story_id": story.get("id", "unknown"),
            "headline": story.get("headline", ""),
            "category": story.get("category", ""),
            "analysis": {
                "raw_content": response_content,
                "provider": self.config.provider,
                "model": self.base_agent.model,
                "cached": True
            },
            "metadata": {
                "processed_at": time.time(),
                "conversation_id": "conversation_context",
                "analysis_type": "multi_perspective"
            }
        }
    
    async def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """End a conversation and return statistics
        
        Args:
            conversation_id: Conversation to end
            
        Returns:
            Conversation statistics
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations.pop(conversation_id)
        
        # Calculate savings from caching
        total_tokens = conversation.total_input_tokens + conversation.total_output_tokens
        cache_hit_ratio = conversation.cache_tokens_read / max(conversation.total_input_tokens, 1)
        
        stats = {
            "conversation_id": conversation_id,
            "stories_processed": conversation.stories_processed,
            "total_messages": len(conversation.messages),
            "duration_minutes": (time.time() - conversation.last_activity) / 60,
            "tokens": {
                "total_input": conversation.total_input_tokens,
                "total_output": conversation.total_output_tokens,
                "cache_created": conversation.cache_tokens_created,
                "cache_read": conversation.cache_tokens_read,
                "cache_hit_ratio": cache_hit_ratio
            },
            "estimated_savings": {
                "without_cache_cost": total_tokens * 0.003,  # Estimated cost
                "with_cache_cost": (
                    conversation.cache_tokens_created * 0.00375 +  # 25% markup for cache writes
                    conversation.cache_tokens_read * 0.0003 +      # 90% discount for cache reads
                    (conversation.total_input_tokens - conversation.cache_tokens_read) * 0.003
                ),
                "savings_ratio": cache_hit_ratio * 0.9  # Approximate savings
            }
        }
        
        return stats
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get current conversation statistics"""
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        conversation = self.active_conversations[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "stories_processed": conversation.stories_processed,
            "messages": len(conversation.messages),
            "last_activity": conversation.last_activity,
            "tokens": {
                "cache_read": conversation.cache_tokens_read,
                "cache_created": conversation.cache_tokens_created,
                "total_input": conversation.total_input_tokens,
                "total_output": conversation.total_output_tokens
            },
            "active_for_minutes": (time.time() - conversation.last_activity) / 60
        }
    
    async def cleanup_old_conversations(self, max_age_minutes: int = 30):
        """Clean up conversations that are too old"""
        current_time = time.time()
        to_remove = []
        
        for conv_id, conversation in self.active_conversations.items():
            age_minutes = (current_time - conversation.last_activity) / 60
            if age_minutes > max_age_minutes:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            await self.end_conversation(conv_id)