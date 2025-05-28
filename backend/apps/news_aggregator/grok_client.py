"""
Grok API client for Django integration
Handles all interactions with the Grok AI API
"""
from typing import Dict, Any, List, Optional, Union, Literal
import httpx
import json
import logging
import asyncio
from datetime import datetime

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GrokClient:
    """Async wrapper for Grok API interactions"""
    
    def __init__(self):
        self.api_key = settings.XAI_API_KEY
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set in settings")
        
        self.base_url = "https://api.x.ai/v1"
        self.timeout = httpx.Timeout(120.0, connect=10.0)
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-3",
        search_params: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Create a completion using the Grok API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (grok-3, grok-3-mini, etc)
            search_params: Optional search parameters for live search
            response_format: Optional JSON schema for structured output
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dict containing the API response
        """
        
        # Build request body
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            request_body["max_tokens"] = max_tokens
            
        if response_format:
            request_body["response_format"] = response_format
            
        # Add search parameters if provided
        if search_params:
            request_body["extra_body"] = {"search_parameters": search_params}
        
        # Log request details
        logger.info(f"Grok API request - Model: {model}, Messages: {len(messages)}")
        if search_params:
            try:
                # Use ensure_ascii=True to avoid Unicode encoding issues on Windows
                search_params_str = json.dumps(search_params, ensure_ascii=False, indent=None)
                logger.debug(f"Search params: {search_params_str}")
            except Exception as e:
                logger.debug(f"Search params logging failed: {e}")
        
        # Make the API call
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=request_body
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Log token usage if available
                if "usage" in result:
                    logger.info(f"Token usage - Prompt: {result['usage'].get('prompt_tokens', 0)}, "
                               f"Completion: {result['usage'].get('completion_tokens', 0)}")
                
                return result
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Grok API HTTP error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Grok API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Grok API request failed: {str(e)}")
                raise
    
    async def create_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        Convenience method for simple chat completions
        
        Returns just the message content as a string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self.create_completion(messages=messages, **kwargs)
        
        # Extract the response content
        return result["choices"][0]["message"]["content"]
    
    async def create_structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        model: str = "grok-3",
        search_enabled: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a completion with structured JSON output
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt containing the content to analyze
            schema: JSON schema for structured output
            model: Model to use (default: grok-3)
            search_enabled: Whether to enable live search (default: False)
            **kwargs: Additional parameters passed to create_completion
        
        Returns:
            The parsed JSON response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": schema,
                "strict": False
            }
        }
        
        # Handle search_enabled parameter
        search_params = None
        if search_enabled:
            # Extract a better search query from the content
            search_query = self._extract_search_query(user_prompt)
            search_params = self.build_search_params(
                query=search_query,
                language="el",
                max_results=10,
                recency_days=7
            )
        
        result = await self.create_completion(
            messages=messages,
            model=model,
            response_format=response_format,
            search_params=search_params,
            **kwargs
        )
        
        # Parse and return the JSON response
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    
    def build_search_params(
        self,
        query: str,
        language: str = "el",
        max_results: int = 5,
        recency_days: Optional[int] = 7
    ) -> Dict[str, Any]:
        """
        Build search parameters for Grok's live search
        
        Args:
            query: Search query
            language: Language code (default: el for Greek)
            max_results: Maximum number of results
            recency_days: Limit results to past N days
            
        Returns:
            Dictionary of search parameters
        """
        params = {
            "query": query,
            "max_results": max_results,
            "search_options": {
                "language": language
            }
        }
        
        # Add recency filter if specified
        if recency_days:
            params["search_options"]["recency_days"] = recency_days
        
        # Add domain exclusions for low-quality sites
        excluded_domains = getattr(settings, 'EXCLUDED_DOMAINS', [])
        if excluded_domains:
            params["search_options"]["exclude_domains"] = excluded_domains
        
        return params
    
    def _extract_search_query(self, user_prompt: str) -> str:
        """
        Extract a good search query from the user prompt
        
        Args:
            user_prompt: The full user prompt
            
        Returns:
            A concise search query for live search
        """
        # Remove common instruction phrases
        content = user_prompt.replace('Ανάλυσε το παρακάτω άρθρο', '')
        content = content.replace('Απάντησε σε JSON', '')
        content = content.replace('με τη δομή που σου δόθηκε', '')
        content = content.replace('Χρησιμοποίησε live search', '')
        
        # Find the actual article content (usually after "άρθρο:")
        lines = content.split('\n')
        article_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.endswith(':') and len(line) > 20:
                article_lines.append(line)
                if len(' '.join(article_lines)) > 150:  # Limit to ~150 chars
                    break
        
        # Join and clean up
        search_query = ' '.join(article_lines)
        
        # Remove ellipsis and extra whitespace
        search_query = search_query.replace('...', '').strip()
        
        # If still too long, take first 150 chars
        if len(search_query) > 150:
            search_query = search_query[:150].rsplit(' ', 1)[0]  # Break at word boundary
        
        return search_query or user_prompt[:100]  # Fallback


# Singleton instance
_grok_client = None

def get_grok_client() -> GrokClient:
    """Get or create the Grok client instance"""
    global _grok_client
    if _grok_client is None:
        _grok_client = GrokClient()
    return _grok_client