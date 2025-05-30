"""Multi-provider agent implementation using OpenAI Agents SDK pattern"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI
from pydantic import BaseModel

try:
    from .base import create_client, get_provider_capabilities, get_default_model
    from ..tracing import trace_manager, SpanType
except ImportError:
    # Fallback for different import contexts
    from agents_v2.providers.base import create_client, get_provider_capabilities, get_default_model
    from agents_v2.tracing import trace_manager, SpanType


class AgentResponse(BaseModel):
    """Standard response format for agents"""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class MultiProviderAgent:
    """Base class for agents that can work with multiple AI providers"""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        provider: str = "grok",
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        """Initialize a multi-provider agent
        
        Args:
            name: Agent name
            instructions: System instructions for the agent
            provider: AI provider to use ('grok', 'anthropic', 'gemini')
            model: Specific model to use (defaults to provider's default)
            tools: List of tool definitions (OpenAI function schema format)
            temperature: Temperature for generation
            max_retries: Number of retries on failure
        """
        self.name = name
        self.instructions = instructions
        self.provider = provider
        self.model = model or get_default_model(provider)
        self.tools = tools or []
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Create client
        self.client = create_client(provider)
        self.capabilities = get_provider_capabilities(provider)
        
    async def run(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """Run the agent with the given input
        
        Args:
            messages: Input messages (string or list of message dicts)
            tools: Override tools for this run
            tool_choice: Tool choice strategy ('auto', 'none', or specific tool)
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Additional arguments for the API call
            
        Returns:
            AgentResponse with the result
        """
        # Start agent span for tracing
        with trace_manager.span(
            SpanType.AGENT, 
            f"{self.name}",
            agent_name=self.name,
            provider=self.provider,
            model=self.model
        ):
            # Prepare messages
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            
            # Add system instructions
            full_messages = [
                {"role": "system", "content": self.instructions}
            ] + messages
            
            # Use provided tools or default agent tools
            tools_to_use = tools or self.tools
            
            # Prepare API call parameters
            params = {
                "model": self.model,
                "messages": full_messages,
                "temperature": self.temperature,
                **kwargs
            }
            
            # Add tools if available and supported
            if tools_to_use and self.capabilities.get("function_calling", False):
                params["tools"] = tools_to_use
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            # Add response format if specified
            if response_format:
                params["response_format"] = response_format
            
            # Handle provider-specific features
            if self.provider == "anthropic" and self.capabilities.get("extended_thinking"):
                # Enable extended thinking for complex tasks
                params["extra_body"] = kwargs.get("extra_body", {})
                
            elif self.provider == "gemini" and self.capabilities.get("reasoning"):
                # Set reasoning effort for Gemini
                params["extra_body"] = {
                    "reasoning_effort": kwargs.get("reasoning_effort", "medium")
                }
            
            # Execute with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    # Trace the generation
                    with trace_manager.span(
                        SpanType.GENERATION,
                        f"Generate with {self.model}",
                        model=self.model,
                        provider=self.provider,
                        attempt=attempt + 1
                    ):
                        response = await self._call_api(params)
                    
                    return AgentResponse(
                        content=response.choices[0].message.content,
                        provider=self.provider,
                        model=self.model,
                        usage=response.usage.model_dump() if response.usage else None,
                        metadata={
                            "finish_reason": response.choices[0].finish_reason,
                            "attempt": attempt + 1
                        }
                    )
                    
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            raise RuntimeError(f"Failed after {self.max_retries} attempts: {last_error}")
    
    async def _call_api(self, params: Dict[str, Any]) -> Any:
        """Make the actual API call (async wrapper)"""
        # OpenAI SDK is sync, so we run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(**params)
        )
    
    def run_sync(
        self,
        messages: Union[str, List[Dict[str, str]]],
        **kwargs
    ) -> AgentResponse:
        """Synchronous version of run()"""
        return asyncio.run(self.run(messages, **kwargs))
    
    async def stream(
        self,
        messages: Union[str, List[Dict[str, str]]],
        **kwargs
    ):
        """Stream responses from the agent
        
        Yields chunks of text as they arrive
        """
        if not self.capabilities.get("streaming", False):
            # Fallback to non-streaming
            response = await self.run(messages, **kwargs)
            yield response.content
            return
        
        # Prepare messages
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        full_messages = [
            {"role": "system", "content": self.instructions}
        ] + messages
        
        params = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "stream": True,
            **kwargs
        }
        
        # Stream response
        stream = await self._stream_api(params)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_api(self, params: Dict[str, Any]):
        """Stream API call (async wrapper)"""
        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(**params)
        )
        
        # Convert sync iterator to async
        for chunk in stream:
            yield chunk