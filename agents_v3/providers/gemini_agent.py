"""Gemini agent with context caching and Google Search integration"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from .base_agent import BaseAgent, AgentConfig, AgentResponse, AgentRole
from ..conversation_logging.conversation_logger import logger, MessageType, LogLevel
from ..utils.prompt_loader import prompt_loader
import logging

module_logger = logging.getLogger(__name__)
from ..utils.enhanced_prompt_loader import enhanced_prompt_loader


class GeminiAgent(BaseAgent):
    """Gemini agent with native SDK, context caching, and Google Search"""
    
    def __init__(self, config: AgentConfig):
        """Initialize Gemini agent
        
        Args:
            config: Agent configuration
        """
        super().__init__(config)
        
        # Set default model if not specified
        if not self.config.model:
            self.config.model = "gemini-2.5-flash-preview-05-20"
        
        # Cache management
        self.cached_content: Optional[types.Content] = None
        self.cache_expiry: Optional[float] = None
        
    def _init_client(self):
        """Initialize Gemini client"""
        import os
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=api_key)
        
        # Pricing information for cost calculation
        self.pricing = {
            "gemini-2.0-flash-exp": {"input": 0.001, "output": 0.008, "cache_discount": 0.75},
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105, "cache_discount": 0.75},
            "gemini-1.5-flash": {"input": 0.00075, "output": 0.003, "cache_discount": 0.75},
            "gemini-2.5-flash-preview-05-20": {"input": 0.00075, "output": 0.003, "cache_discount": 0.75}
        }
    
    async def start_conversation(self, conversation_type: str = "analysis") -> str:
        """Start a new conversation with cached system context
        
        Args:
            conversation_type: Type of conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = f"gemini_{conversation_type}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Log conversation start
        logger.start_conversation(
            agent_name=self.config.name,
            provider="gemini",
            conversation_type=conversation_type,
            metadata={
                "model": self.config.model,
                "cache_enabled": self.config.cache_system_prompt,
                "search_enabled": self.config.enable_search
            }
        )
        
        # Initialize conversation state
        self.active_conversations[conversation_id] = {
            "messages": [],
            "stories_processed": 0,
            "cache_hits": 0,
            "last_activity": time.time(),
            "conversation_type": conversation_type
        }
        
        # Create cached system content if enabled
        if self.config.cache_system_prompt:
            await self._create_cached_system_prompt(conversation_id)
        
        # For discovery agents, don't send initialization message
        # They will get their specific discovery prompt directly
        if self.config.role == AgentRole.DISCOVERY:
            return conversation_id
        
        # Send initial message using centralized prompt for non-discovery agents
        search_line = "\n  - Real-time search capabilities" if self.config.enable_search else ""
        initial_message = enhanced_prompt_loader.render_prompt(
            "conversation_initialization",
            {
                "conversation_type": conversation_type,
                "agent_role": self.config.role.value,
                "search_enabled": self.config.enable_search,
                "search_line": search_line
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
            provider="gemini",
            message_type=MessageType.SYSTEM,
            content="Conversation initialized with cached system prompt",
            level=LogLevel.INFO,
            cache_hit=self.cached_content is not None
        )
        
        return conversation_id
    
    async def _create_cached_system_prompt(self, conversation_id: str):
        """Create cached system prompt for context reuse"""
        
        # Build system prompt based on agent role
        if self.config.role == AgentRole.DISCOVERY:
            # Discovery agents get simple search-focused instructions
            search_note = "Use Google Search to find the most current news stories." if self.config.enable_search else "Use your knowledge of current events."
            system_instructions = f"""You are a news discovery agent. Your role is to find and format current news stories.

{search_note}

You will receive specific discovery prompts with formatting requirements. Follow them exactly."""
        else:
            # Other agents get the full analysis framework
            framework_content = enhanced_prompt_loader.render_prompt("analysis_framework")
            search_note = "Use Google Search to find current information, verify claims, and discover additional perspectives." if self.config.enable_search else "Work with provided information and existing knowledge."
            
            system_instructions = f"""{self.config.instructions}

{framework_content}

# Search Integration
{search_note}

Ready to analyze stories with thorough, multi-perspective approach."""
        
        try:
            # Create cached content for context reuse
            cache_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=system_instructions)]
            )
            
            # Cache the content (Gemini handles caching automatically for repeated content)
            self.cached_content = cache_content
            self.cache_expiry = time.time() + (60 * 60)  # 1 hour cache
            
            logger.log_message(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="gemini",
                message_type=MessageType.SYSTEM,
                content=f"System prompt cached ({len(system_instructions)} chars)",
                level=LogLevel.INFO,
                cache_hit=False,
                cache_tokens_written=len(system_instructions.split()) * 1.3  # Rough estimate
            )
            
        except Exception as e:
            logger.log_error(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="gemini",
                error_message=f"Failed to cache system prompt: {str(e)}"
            )
            self.cached_content = None
    
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
        """Send message with caching optimization"""
        
        conversation = self.active_conversations[conversation_id]
        start_time = time.time()
        
        try:
            # Build content list for API call
            contents = []
            
            # Add cached system content if available and valid
            cache_hit = False
            if self.cached_content and self.cache_expiry and time.time() < self.cache_expiry:
                contents.append(self.cached_content)
                cache_hit = True
            
            # Add conversation history
            for msg in conversation["messages"]:
                # Convert assistant role to model for Gemini API
                role = "model" if msg["role"] == "assistant" else msg["role"]
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                ))
            
            # Add current message
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)]
            ))
            
            # Setup tools if search is enabled
            tools = []
            if self.config.enable_search:
                tools.append(types.Tool(google_search=types.GoogleSearch()))
            
            # Configure generation
            generate_config = types.GenerateContentConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                response_mime_type="text/plain"
            )
            
            if tools:
                generate_config.tools = tools
            
            # Make async API call
            response = await self.client.aio.models.generate_content(
                model=self.config.model,
                contents=contents,
                config=generate_config
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response content
            response_content = ""
            citations = []
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    response_content = "".join(
                        part.text for part in candidate.content.parts 
                        if hasattr(part, 'text') and part.text
                    )
                
                # Extract citations from grounding metadata
                search_queries = []
                grounding_supports = []
                
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding = candidate.grounding_metadata
                    
                    # Extract search queries used (with null check)
                    if hasattr(grounding, 'web_search_queries') and grounding.web_search_queries:
                        search_queries = list(grounding.web_search_queries)
                    
                    # Extract grounding chunks (sources) with null checks
                    if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                        for chunk in grounding.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                citations.append({
                                    'url': chunk.web.uri if hasattr(chunk.web, 'uri') else '',
                                    'title': chunk.web.title if hasattr(chunk.web, 'title') else 'Untitled'
                                })
                    
                    # Extract grounding supports (which text is supported by which sources)
                    if hasattr(grounding, 'grounding_supports') and grounding.grounding_supports:
                        for support in grounding.grounding_supports:
                            if hasattr(support, 'segment') and support.segment:
                                segment_info = {
                                    'text': support.segment.text if hasattr(support.segment, 'text') else '',
                                    'start_index': getattr(support.segment, 'start_index', 0),
                                    'end_index': getattr(support.segment, 'end_index', 0)
                                }
                                if hasattr(support, 'grounding_chunk_indices') and support.grounding_chunk_indices:
                                    segment_info['source_indices'] = list(support.grounding_chunk_indices)
                                if hasattr(support, 'confidence_scores') and support.confidence_scores:
                                    segment_info['confidence_scores'] = list(support.confidence_scores)
                                grounding_supports.append(segment_info)
            
            # Calculate token usage
            tokens_used = self._extract_token_usage(response)
            
            # Update conversation state
            conversation["messages"].extend([
                {"role": "user", "content": message},
                {"role": "model", "content": response_content}
            ])
            conversation["last_activity"] = time.time()
            if cache_hit:
                conversation["cache_hits"] += 1
            
            # Log the interaction
            if not is_system_init:
                logger.log_message(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="gemini",
                    message_type=MessageType.USER,
                    content=message[:200] + "..." if len(message) > 200 else message,
                    role="user",
                    level=LogLevel.INFO
                )
            
            logger.log_message(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="gemini",
                message_type=MessageType.ASSISTANT,
                content=response_content[:200] + "..." if len(response_content) > 200 else response_content,
                role="model",
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                cost_estimate=0.0,
                cache_hit=cache_hit,
                level=LogLevel.INFO
            )
            
            # Create standardized response with citations
            metadata = {
                "finish_reason": getattr(response.candidates[0], 'finish_reason', None) if response.candidates else None,
                "search_enabled": self.config.enable_search,
                "tools_used": len(tools) > 0
            }
            
            # Add citations to metadata if found
            if citations:
                metadata["citations"] = citations
                metadata["search_queries"] = search_queries if 'search_queries' in locals() else []
                metadata["grounding_supports"] = grounding_supports if 'grounding_supports' in locals() else []
                
                # Log citations for audit
                module_logger.info(f"Gemini {self.config.name} found {len(citations)} citations")
                for i, citation in enumerate(citations[:3]):  # Log first 3
                    module_logger.debug(f"  Citation {i+1}: {citation['title']} - {citation['url'][:50]}...")
            
            return AgentResponse(
                content=response_content,
                provider="gemini",
                model=self.config.model,
                conversation_id=conversation_id,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                cost_estimate=0.0,
                cache_hit=cache_hit,
                cache_tokens_read=tokens_used.get("cache_read", 0) if cache_hit else 0,
                metadata=metadata
            )
            
        except Exception as e:
            error_message = str(e)
            logger.log_error(
                conversation_id=conversation_id,
                agent_name=self.config.name,
                provider="gemini",
                error_message=error_message,
                context={"message_preview": message[:100]}
            )
            
            return AgentResponse(
                content="",
                provider="gemini",
                model=self.config.model,
                conversation_id=conversation_id,
                error=error_message
            )
    
    async def process_story_batch(
        self,
        conversation_id: str,
        stories: List[Dict[str, Any]]
    ) -> List[AgentResponse]:
        """Process multiple stories in conversation with caching benefits
        
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
            provider="gemini",
            message_type=MessageType.SYSTEM,
            content=f"Processing batch of {len(stories)} stories",
            level=LogLevel.INFO,
            batch_info={"story_count": len(stories), "batch_start": True}
        )
        
        for i, story in enumerate(stories):
            try:
                # Create story analysis prompt
                story_prompt = self._create_story_analysis_prompt(story, i + 1, len(stories))
                
                # Process story with conversation context
                response = await self._send_cached_message(
                    conversation_id,
                    story_prompt,
                    cache_message=True
                )
                
                # Update story tracking
                conversation["stories_processed"] += 1
                
                # Log story completion
                logger.log_story_analysis(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="gemini",
                    story_id=story.get("id", f"story_{i}"),
                    headline=story.get("headline", "Unknown"),
                    analysis_result=response.content,
                    analysis_type=self.config.role.value,
                    tokens_used=response.tokens_used or {},
                    response_time_ms=response.response_time_ms or 0,
                    cost_estimate=response.cost_estimate or 0.0,
                    cache_hit=response.cache_hit
                )
                
                results.append(response)
                
            except Exception as e:
                # Handle individual story errors gracefully
                error_response = AgentResponse(
                    content="",
                    provider="gemini",
                    model=self.config.model,
                    conversation_id=conversation_id,
                    error=str(e),
                    metadata={"story_id": story.get("id", f"story_{i}")}
                )
                results.append(error_response)
                
                logger.log_error(
                    conversation_id=conversation_id,
                    agent_name=self.config.name,
                    provider="gemini",
                    error_message=str(e),
                    context={
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
            Conversation statistics
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations.pop(conversation_id)
        
        # Calculate final statistics
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
            "provider": "gemini",
            "model": self.config.model
        }
        
        # Log conversation end
        logger.end_conversation(
            conversation_id=conversation_id,
            agent_name=self.config.name,
            provider="gemini",
            final_stats=stats
        )
        
        return stats
    
    async def _search_web_impl(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Implement web search using Google Search integration
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        if not self.config.enable_search:
            raise ValueError("Search not enabled for this agent")
        
        try:
            # Create a simple conversation for search
            search_conversation_id = f"search_{int(time.time())}"
            
            # Use centralized search prompt if available, otherwise use simple format
            search_prompt = f"""Search for: {query}

Provide structured results with:
1. Title and URL
2. Content summary  
3. Relevance
4. Key information

Focus on recent, reliable sources."""
            
            # Temporary conversation for search
            self.active_conversations[search_conversation_id] = {
                "messages": [],
                "stories_processed": 0,
                    "cache_hits": 0,
                "last_activity": time.time()
            }
            
            response = await self._send_cached_message(
                search_conversation_id,
                search_prompt,
                cache_message=False
            )
            
            # Clean up search conversation
            del self.active_conversations[search_conversation_id]
            
            # Parse response into structured results
            # Note: This is a simplified version - in practice you'd want more sophisticated parsing
            results = [{
                "title": "Search Results",
                "url": "gemini://search",
                "content": response.content,
                "relevance": "high",
                "source": "google_search_via_gemini"
            }]
            
            return results
            
        except Exception as e:
            logger.log_error(
                conversation_id="search",
                agent_name=self.config.name,
                provider="gemini",
                error_message=f"Search failed: {str(e)}",
                context={"query": query}
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
        """Create comprehensive story analysis prompt"""
        
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
        
        # Add search integration note for Gemini
        if self.config.enable_search:
            prompt += "\n\n**Real-time Research**: Use Google Search to find latest information, verify facts, and discover additional perspectives."
        
        return prompt
    
    def _extract_token_usage(self, response) -> Dict[str, int]:
        """Extract token usage from Gemini response"""
        try:
            usage = getattr(response, 'usage_metadata', None)
            if usage:
                return {
                    "input": getattr(usage, 'prompt_token_count', 0),
                    "output": getattr(usage, 'candidates_token_count', 0),
                    "total": getattr(usage, 'total_token_count', 0),
                    "cache_read": getattr(usage, 'cached_content_token_count', 0)
                }
            else:
                # Rough estimation if usage data not available
                return {
                    "input": 1000,  # Estimate
                    "output": 500,  # Estimate
                    "total": 1500,
                    "cache_read": 0
                }
        except Exception:
            return {"input": 1000, "output": 500, "total": 1500, "cache_read": 0}