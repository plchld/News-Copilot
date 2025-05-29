"""
Claude API client for Django integration
Handles all interactions with the Claude AI API with websearch, caching and async support
"""
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
import os
from datetime import datetime
import json

from django.conf import settings
from django.core.cache import cache
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Async wrapper for Claude API interactions with websearch and caching"""
    
    def __init__(self):
        # Check for API key in Django settings first, then environment
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None) or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in settings or environment variables")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.timeout = 120.0
        
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        cache_control: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a completion using the Claude API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Claude model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Optional tools like web search
            cache_control: Optional cache control for prompt caching
            
        Returns:
            Dict containing the API response
        """
        
        # Build request params
        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if tools:
            request_params["tools"] = tools
            
        # Add cache control to last user message if specified
        if cache_control and messages:
            # Find the last user message and add cache control
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    if isinstance(messages[i]["content"], str):
                        messages[i]["content"] = [
                            {"type": "text", "text": messages[i]["content"]}
                        ]
                    # Add cache control to the last content block
                    if isinstance(messages[i]["content"], list) and messages[i]["content"]:
                        messages[i]["content"][-1]["cache_control"] = cache_control
                    break
        
        # Log request details
        logger.info(f"Claude API request - Model: {model}, Messages: {len(messages)}")
        if tools:
            logger.debug(f"Tools enabled: {[tool.get('type', 'unknown') for tool in tools]}")
        
        # Make the API call
        try:
            response = await self.client.messages.create(**request_params)
            
            # Log token usage if available
            if hasattr(response, 'usage'):
                logger.info(f"Token usage - Input: {response.usage.input_tokens}, "
                           f"Output: {response.usage.output_tokens}")
                if hasattr(response.usage, 'cache_read_input_tokens'):
                    logger.info(f"Cache read tokens: {response.usage.cache_read_input_tokens}")
            
            return {
                "content": response.content,
                "usage": response.usage.__dict__ if hasattr(response, 'usage') else {},
                "model": response.model if hasattr(response, 'model') else model,
                "stop_reason": response.stop_reason if hasattr(response, 'stop_reason') else None
            }
            
        except Exception as e:
            logger.error(f"Claude API request failed: {str(e)}")
            raise
    
    async def create_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-3-7-sonnet-20250219",
        use_websearch: bool = False,
        **kwargs
    ) -> str:
        """
        Convenience method for simple chat completions
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt containing the content to analyze
            model: Claude model to use
            use_websearch: Whether to enable web search
            **kwargs: Additional parameters
            
        Returns:
            The response content as a string
        """
        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        # Add web search tool if requested
        tools = None
        if use_websearch:
            tools = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
                "user_location": {
                    "type": "approximate",
                    "city": "Athens",
                    "region": "Greece",
                    "timezone": "Europe/Athens"
                }
            }]
        
        # Build request params with system prompt at top level
        request_params = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        # Add system prompt at top level
        if system_prompt:
            request_params["system"] = system_prompt
            
        if tools:
            request_params["tools"] = tools
        
        # Use the client directly for proper system message handling
        response = await self.client.messages.create(**request_params)
        
        # DEBUG: Log full response structure
        logger.info(f"Full Claude response: {response}")
        logger.info(f"Response content: {response.content}")
        logger.info(f"Response usage: {getattr(response, 'usage', 'No usage')}")
        logger.info(f"Response stop_reason: {getattr(response, 'stop_reason', 'No stop_reason')}")
        
        # Extract the response content - handle multiple content blocks for web search
        if response.content and len(response.content) > 0:
            # For web search responses, concatenate all text blocks
            full_response = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    full_response += content_block.text
            return full_response if full_response else response.content[0].text
        return ""
    
    async def create_structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        model: str = "claude-3-7-sonnet-20250219",
        use_websearch: bool = False,
        use_caching: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a completion with structured JSON output
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt containing the content to analyze
            schema: JSON schema for structured output (will be added to system prompt)
            model: Claude model to use
            use_websearch: Whether to enable web search
            use_caching: Whether to enable prompt caching
            **kwargs: Additional parameters
            
        Returns:
            The parsed JSON response
        """
        
        # Enhance system prompt with JSON schema requirements
        enhanced_system_prompt = f"""{system_prompt}

Πρέπει να απαντήσεις σε έγκυρο JSON format που να ακολουθεί αυστηρά αυτό το schema:

{json.dumps(schema, ensure_ascii=False, indent=2)}

Σημαντικό: Η απάντησή σου πρέπει να είναι μόνο το JSON object, χωρίς επιπλέον κείμενο πριν ή μετά."""

        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        # Add web search tool if requested
        tools = None
        if use_websearch:
            tools = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
                "user_location": {
                    "type": "approximate",
                    "city": "Athens",
                    "region": "Greece",
                    "timezone": "Europe/Athens"
                }
            }]
        
        # Add cache control to user message if requested
        if use_caching and messages:
            if isinstance(messages[-1]["content"], str):
                messages[-1]["content"] = [
                    {"type": "text", "text": messages[-1]["content"], "cache_control": {"type": "ephemeral"}}
                ]
        
        # Build request params with system prompt at top level
        request_params = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "system": enhanced_system_prompt
        }
        
        if tools:
            request_params["tools"] = tools
        
        # Use the client directly for proper system message handling
        response = await self.client.messages.create(**request_params)
        
        # Extract and parse the JSON response
        if response.content and len(response.content) > 0:
            content = response.content[0].text
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON response from Claude: {e}")
        
        raise ValueError("Empty response from Claude")
    
    def get_cache_key(self, prompt_hash: str, model: str) -> str:
        """Generate cache key for prompt caching"""
        return f"claude:cache:{model}:{prompt_hash}"
    
    def cache_conversation(self, cache_key: str, messages: List[Dict[str, str]], timeout: int = 3600):
        """Cache conversation for prompt caching"""
        cache.set(cache_key, messages, timeout)
    
    def get_cached_conversation(self, cache_key: str) -> Optional[List[Dict[str, str]]]:
        """Get cached conversation"""
        return cache.get(cache_key)


# Singleton instance
_claude_client = None

def get_claude_client() -> ClaudeClient:
    """Get or create the Claude client instance"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client