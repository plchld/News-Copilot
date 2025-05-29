# Multi-Model Web Search Integration Guide

## Overview

This guide documents how different LLM providers implement web search functionality and their API differences for integration into the News Copilot agent system.

## Supported Providers & Models

### 1. Anthropic Claude

#### Available Models with Web Search
- **Claude Opus 4** (`claude-opus-4-20250514`) -> Only for the most depanding tasks that require a lot of reasoning or intelligent agent coordination
- **Claude Sonnet 4** (`claude-sonnet-4-20250514`) -> main prod model
- **Claude Sonnet 3.7** (`claude-3-7-sonnet-20250219`) -> main testing model
- **Claude Haiku 3.5** (`claude-3-5-haiku-latest`) -> small model for things that are easy.

#### Web Search Implementation

**Asynchronous**:
```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

response = await client.messages.create(
    model="claude-3-7-sonnet-latest",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Search query"}],
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
        "allowed_domains": ["example.com"],  # Optional
        "blocked_domains": ["spam.com"],     # Optional
        "user_location": {                   # Optional
            "type": "approximate",
            "city": "Athens",
            "country": "GR",
            "timezone": "Europe/Athens"
        }
    }]
)
```

**Streaming**:
```python
stream = await client.messages.create(
    model="claude-3-7-sonnet-latest",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Search for AI developments"}],
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    stream=True
)

async for event in stream:
    if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
        print(event.delta.text, end="")
```

**Prompt Caching with Web Search**:
```python
import anthropic

client = anthropic.Anthropic()

# First request with web search and cache breakpoint
messages = [
    {
        "role": "user",
        "content": "What's the current weather in San Francisco today?"
    }
]

response1 = client.messages.create(
    model="claude-3-7-sonnet-latest",
    max_tokens=1024,
    messages=messages,
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "user_location": {
            "type": "approximate",
            "city": "San Francisco",
            "region": "California",
            "country": "US",
            "timezone": "America/Los_Angeles"
        }
    }]
)

# Add Claude's response to the conversation
messages.append({
    "role": "assistant",
    "content": response1.content
})

# Second request with cache breakpoint after the search results
messages.append({
    "role": "user",
    "content": "Should I expect rain later this week?",
    "cache_control": {"type": "ephemeral"}  # Cache up to this point
})

response2 = client.messages.create(
    model="claude-3-7-sonnet-latest",
    max_tokens=1024,
    messages=messages,
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "user_location": {
            "type": "approximate",
            "city": "San Francisco",
            "region": "California",
            "country": "US",
            "timezone": "America/Los_Angeles"
        }
    }]
)

# Check cache usage
print(f"Cache read tokens: {response2.usage.get('cache_read_input_tokens', 0)}")
```

**Batch Processing with Web Search**:
```python
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

client = anthropic.Anthropic()

# Create batch with multiple web search requests
message_batch = client.messages.batches.create(
    requests=[
        Request(
            custom_id="article-analysis-1",
            params=MessageCreateParamsNonStreaming(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": "Analyze recent developments in AI safety regulations"
                }],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3
                }]
            )
        ),
        Request(
            custom_id="article-analysis-2", 
            params=MessageCreateParamsNonStreaming(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": "Find alternative viewpoints on climate change policies"
                }],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                    "blocked_domains": ["spam.com"]
                }]
            )
        )
    ]
)

# Monitor batch status
batch_status = client.messages.batches.retrieve(message_batch.id)
print(f"Batch status: {batch_status.processing_status}")

# Process results when ready
if batch_status.processing_status == "ended":
    for result in client.messages.batches.results(message_batch.id):
        if result.result.type == "succeeded":
            print(f"Success for {result.custom_id}")
            print(result.result.message.content[0].text)
        elif result.result.type == "errored":
            print(f"Error for {result.custom_id}: {result.result.error}")
```

#### Key Features
- **Automatic Search Decision**: Claude decides when to search
- **Domain Filtering**: Allow/block specific domains
- **Geographic Localization**: Location-based search results
- **Automatic Citations**: Source links included
- **Native Async & Streaming**: Full async support
- **Prompt Caching**: Efficient caching for multi-turn conversations with search results
- **Batch Processing**: 50% cost reduction for bulk operations, up to 100k requests per batch

#### Pricing
- **$10 per 1,000 searches** + standard token costs

### 2. Google Gemini

#### Available Models with Web Search
- **Gemini 2.5 Pro** (`gemini-2.5-pro-preview-05-06`)
- **Gemini 2.5 Flash** (`gemini-2.5-flash-preview-05-20`)

#### Web Search Implementation

```python
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

client = genai.Client()

# Async
response = await client.aio.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents="Search query",
    config=GenerateContentConfig(
        tools=[Tool(google_search=GoogleSearch())],
        response_modalities=["TEXT"]
    )
)

# Sync
response = client.models.generate_content(
    model="gemini-2.5-pro-preview-05-06",
    contents="Search query",
    config=GenerateContentConfig(
        tools=[Tool(google_search=GoogleSearch())],
        response_modalities=["TEXT"]
    )
)
```

#### Key Features
- **Dynamic Search Decision**: Model decides when to search
- **Grounding Metadata**: Rich source metadata
- **Native Async Support**: Via `client.aio` namespace
- **No Streaming**: Streaming not supported

#### Pricing
- **1,500 free searches/day** on paid tier
- **$35 per 1,000 additional searches**

### 3. X.AI Grok

#### Available Models
- **Grok 3** (`grok-3-latest`)
- **Grok 3 Fast** (`grok-3-fast`) 
- **Grok 3 Mini** (`grok-3-mini`)

#### Web Search Implementation

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Async
response = await client.chat.completions.create(
    model="grok-3-latest",
    messages=[{"role": "user", "content": "Search query"}],
    extra_body={
        "search_parameters": {
            "mode": "on",
            "sources": [{"type": "news"}, {"type": "web"}],
            "excluded_websites_map": {"spam.com": "low quality"},
            "max_results": 15
        }
    }
)

# Streaming
stream = await client.chat.completions.create(
    model="grok-3-fast",
    messages=[{"role": "user", "content": "Search query"}],
    extra_body={"search_parameters": {"mode": "on"}},
    stream=True
)

async for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Key Features
- **Manual Search Control**: Explicit search activation
- **Source Type Control**: News, web, X (Twitter) sources
- **Domain Exclusion**: Block domains with reasons
- **Native Async & Streaming**: Full async support
- **Greek Optimization**: Pre-tuned prompts for Greek content

#### Pricing
- Search included in token costs

## API Comparison Matrix

| Feature | Claude | Gemini | Grok |
|---------|--------|--------|------|
| **Async Support** | ✅ Native | ✅ Native | ✅ Native |
| **Streaming** | ✅ Event-based | ❌ Not supported | ✅ Chunk-based |
| **Search Decision** | 🤖 Automatic | 🤖 Dynamic | ⚙️ Manual |
| **Domain Filtering** | ✅ Allow/Block | ❌ Not supported | ✅ Exclusion map |
| **Localization** | ✅ Geographic | ❌ Not supported | ❌ Not supported |
| **Citations** | ✅ Automatic | ✅ Grounding metadata | ⚠️ In content |
| **Cost Model** | Per search + tokens | Per search + tokens | Tokens only |

## Agent Integration

### Model Configuration

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

class ModelProvider(Enum):
    GROK = "grok"
    CLAUDE = "claude" 
    GEMINI = "gemini"

class ModelType(Enum):
    # Grok Models
    GROK_3_MINI = "grok-3-mini"
    GROK_3 = "grok-3-latest"
    GROK_3_FAST = "grok-3-fast"
    
    # Claude Models  
    CLAUDE_OPUS_4 = "claude-opus-4-20250514"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    CLAUDE_SONNET_3_7 = "claude-3-7-sonnet-20250219"
    CLAUDE_SONNET_3_5 = "claude-3-5-sonnet-latest"
    CLAUDE_HAIKU_3_5 = "claude-3-5-haiku-latest"
    
    # Gemini Models
    GEMINI_2_5_PRO = "gemini-2.5-pro-preview-05-06"
    GEMINI_2_5_FLASH = "gemini-2.5-flash-preview-05-20"

@dataclass
class WebSearchConfig:
    enabled: bool = True
    max_searches: int = 5
    max_results: int = 15
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    localization: Optional[Dict[str, str]] = None
    
@dataclass 
class ModelConfig:
    model_type: ModelType
    provider: ModelProvider
    supports_web_search: bool
    supports_async: bool
    supports_streaming: bool
    web_search_config: Optional[WebSearchConfig] = None
    cost_per_1k_tokens: float = 0.0
    cost_per_search: float = 0.0
```

### Multi-Provider Agent

```python
class MultiModelAgent:
    def __init__(self, clients: Dict[ModelProvider, Any]):
        self.clients = clients
        self.model_configs = {
            # Grok
            ModelType.GROK_3: ModelConfig(
                model_type=ModelType.GROK_3,
                provider=ModelProvider.GROK,
                supports_web_search=True,
                supports_async=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.002
            ),
            
            # Claude
            ModelType.CLAUDE_SONNET_3_7: ModelConfig(
                model_type=ModelType.CLAUDE_SONNET_3_7,
                provider=ModelProvider.CLAUDE,
                supports_web_search=True,
                supports_async=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.003,
                cost_per_search=0.01
            ),
            
            # Gemini
            ModelType.GEMINI_2_5_FLASH: ModelConfig(
                model_type=ModelType.GEMINI_2_5_FLASH,
                provider=ModelProvider.GEMINI,
                supports_web_search=True,
                supports_async=True,
                supports_streaming=False,
                cost_per_1k_tokens=0.001,
                cost_per_search=0.035
            )
        }
    
    async def call_model_with_search(self, model_type: ModelType, prompt: str, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        provider = self.model_configs[model_type].provider
        
        if provider == ModelProvider.GROK:
            return await self._call_grok(model_type, prompt, context)
        elif provider == ModelProvider.CLAUDE:
            return await self._call_claude(model_type, prompt, context)
        elif provider == ModelProvider.GEMINI:
            return await self._call_gemini(model_type, prompt, context)
    
    async def _call_grok(self, model_type: ModelType, prompt: str, context: Dict[str, Any]):
        client = self.clients[ModelProvider.GROK]
        
        response = await client.chat.completions.create(
            model=model_type.value,
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "search_parameters": {
                    "mode": "on",
                    "sources": [{"type": "news"}, {"type": "web"}],
                    "max_results": 15
                }
            }
        )
        
        return {
            'data': response.choices[0].message.content,
            'tokens_used': response.usage.total_tokens,
            'provider': ModelProvider.GROK
        }
    
    async def _call_claude(self, model_type: ModelType, prompt: str, context: Dict[str, Any]):
        client = self.clients[ModelProvider.CLAUDE]
        
        response = await client.messages.create(
            model=model_type.value,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        
        return {
            'data': response.content[0].text,
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
            'provider': ModelProvider.CLAUDE
        }
    
    async def _call_gemini(self, model_type: ModelType, prompt: str, context: Dict[str, Any]):
        from google import genai
        from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
        
        client = self.clients[ModelProvider.GEMINI]
        
        response = await client.aio.models.generate_content(
            model=model_type.value,
            contents=prompt,
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )
        
        return {
            'data': response.candidates[0].content.parts[0].text,
            'tokens_used': getattr(response, 'usage_metadata', {}).get('total_token_count', 0),
            'provider': ModelProvider.GEMINI
        }
```

## Best Practices

### Model Selection
- **High Accuracy**: Claude Sonnet 4
- **Cost Efficiency**: Gemini 2.5 Flash
- **Real-time**: Grok 3 Fast
- **Greek Content**: Use Greek-optimized prompts (Grok has pre-tuned prompts)

### Search Optimization
- **Domain Exclusion**: Exclude original article's domain
- **Localization**: Use Greek localization (Claude only)
- **Result Limits**: 10-15 results optimal

### Async Implementation
- **Claude**: `AsyncAnthropic`
- **Grok**: `AsyncOpenAI`
- **Gemini**: `client.aio.models.generate_content()`

### Error Handling
- Implement fallback models
- Monitor costs per request
- Handle search API failures gracefully