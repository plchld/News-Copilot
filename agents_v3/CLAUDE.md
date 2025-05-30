# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The agents_v3 system is a sophisticated AI-powered news intelligence platform that implements **conversation isolation** and direct agent communication. This system uses native SDKs (Anthropic and Gemini) to create specialized agents that collaborate on multi-perspective news analysis while maintaining separate conversation contexts to prevent contamination.

## Architecture

### Core Principles

1. **Conversation Isolation**: Each agent pair maintains completely separate conversation threads
2. **Request Queueing**: Sequential processing prevents concurrent access issues  
3. **Direct Communication**: No broadcasts - agents request specific information from other agents
4. **External Prompts**: All agent instructions stored in markdown files under `prompts/`
5. **Native SDKs**: Direct usage of provider-specific features (caching, search, etc.)

### Directory Structure

```
agents_v3/
├── providers/              # Native SDK agent implementations
│   ├── base_agent.py      # Abstract base class with conversation isolation
│   ├── anthropic_agent.py # Claude with cache control blocks
│   ├── gemini_agent.py    # Gemini with Google Search
│   └── anthropic_agent_broken.py # Backup implementation
├── orchestration/         # Pipeline orchestration
│   └── conversational_orchestrator.py # Main orchestrator
├── communication/         # Inter-agent messaging
│   └── agent_message_bus.py # Message routing and queueing
├── conversation_logging/  # Logging and debugging
│   ├── conversation_logger.py
│   └── agent_conversation_logger.py
├── prompts/              # External agent prompts
│   ├── discovery_agent.md
│   ├── greek_perspective_agent.md
│   ├── international_perspective_agent.md
│   ├── fact_verification_agent.md
│   └── synthesis_agent.md
├── utils/               # Utilities
│   └── prompt_loader.py # Load prompts from external files
├── examples/           # Usage examples and tests
├── tests/             # Test suite
├── logs/              # Conversation logs (JSON)
└── debug_logs/        # Human-readable debug logs
```

## Key Components

### BaseAgent (providers/base_agent.py)

The foundation class implementing conversation isolation:

- **Isolated Conversations**: `isolated_conversations` dict maps requesting_agent → conversation_id
- **Request Queueing**: `request_queue` ensures sequential processing 
- **Message Handling**: `handle_analysis_request()` queues requests to prevent concurrent access
- **Cost Calculation**: Provider-specific pricing for Anthropic, Gemini, OpenAI

Key methods:
- `_get_isolated_conversation()`: Creates/retrieves isolated conversation per requesting agent
- `_process_request_queue()`: Processes requests sequentially 
- `handle_analysis_request()`: Queue entry point for inter-agent requests

### AnthropicAgent (providers/anthropic_agent.py)

Claude implementation with advanced caching:

- **Cache Control Blocks**: Ephemeral caching with configurable TTL (5m or 1h)
- **System Prompt Caching**: `_build_cached_system_prompt()` creates cacheable instructions
- **Extended TTL Support**: Beta header for 1-hour cache duration
- **Token Usage Tracking**: Detailed cache hit/miss metrics

Key features:
- Cache control blocks for conversation history
- System prompt with analysis framework caching
- Comprehensive token usage and cost tracking

### GeminiAgent (providers/gemini_agent.py)

Gemini implementation with Google Search:

- **Context Caching**: Native Gemini context caching with TTL
- **Google Search Integration**: Real-time search for discovery and fact-checking
- **Search Parameter Building**: Intelligent query construction with domain filtering

### ConversationalOrchestrator (orchestration/conversational_orchestrator.py)

Main system coordinator implementing the conversation flow:

**Agent Configuration**:
- Discovery: Gemini + Google Search (gemini-2.5-flash-preview-05-20)
- Analysis: Anthropic Claude (claude-3-5-haiku-latest)
- Specialized agents for Greek perspective, international perspective, fact verification, synthesis

**Conversation Flow**:
1. **Discovery Phase**: Gemini agent discovers stories (no broadcast)
2. **Agent Conversations**: Sequential agent interactions using isolated conversations
3. **Output Persistence**: Each agent's analysis saved to timestamped .md files

Key methods:
- `analyze_news_batch()`: Main entry point for news analysis
- `_phase_discovery_initial()`: Discovery without broadcasting
- `_conduct_agent_conversations()`: Manage isolated agent conversations
- `_save_agent_output()`: Save agent results to markdown files

### AgentMessageBus (communication/agent_message_bus.py)

Inter-agent communication system:

- **Message Routing**: Routes requests between agents using agent IDs
- **Response Tracking**: Manages request-response correlation with futures
- **Timeout Handling**: Configurable timeouts for agent responses
- **Message History**: Comprehensive logging of all inter-agent communications

Key features:
- `request_analysis()`: Request analysis from target agent
- `send_message()`: Route messages with response tracking
- Background message processing loop

## Development Commands

### Environment Setup

```bash
# Set required API keys
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"

# Install dependencies
pip install anthropic google-genai asyncio
```

### Running Tests and Examples

```bash
# Simple 2-story analysis test
cd agents_v3/examples
python test_simple_analysis.py

# Test with different parameters (edit the file):
# STORY_COUNT = 5
# CATEGORIES = ["Politics", "Economy"] 
# TOPICS = ["Greece", "EU", "Elections"]

# Test without API keys (mock system)
python test_system_no_api.py

# Full demo with more stories
python news_analysis_demo.py

# Test agent communication specifically
cd agents_v3/tests
python test_agent_communication.py

# Test basic functionality without APIs
python test_basic_functionality.py
```

### Configuration Options

Edit `test_simple_analysis.py` for quick parameter tuning:

```python
# Easy to modify parameters
STORY_COUNT = 2  # Number of stories to analyze
CATEGORIES = ["Technology", "Politics"]  # Story categories
TOPICS = ["AI", "Machine Learning", "Elections"]  # Specific topics

# Other theme options:
# CATEGORIES = ["Economy", "International"] + TOPICS = ["Trade", "Markets", "EU"]
# CATEGORIES = ["Health", "Environment"] + TOPICS = ["Climate", "Medicine", "Policy"] 
# CATEGORIES = ["Greece", "Politics"] + TOPICS = ["New Democracy", "SYRIZA", "Elections"]
```

### Log Analysis

```bash
# Analyze conversation logs
cd agents_v3/tools
python analyze_logs.py

# Logs are saved in multiple formats:
# - debug_logs/*.md: Human-readable conversation flow
# - debug_logs/*.txt: Simple text format
# - logs/agent_conversations/*.json: Machine-readable logs
```

### Output Files

Agent outputs are automatically saved to timestamped files:

```bash
# Check agent outputs
ls agents_v3/outputs/
# Example: 20241230_153045_discovery_agent_news_123.md

# View conversation logs  
ls agents_v3/debug_logs/
# Example: 20241230_153045_news_analysis_conversation_debug.md
```

## Adding New Agents

1. **Create Agent Class**: Extend `BaseAgent` in `providers/`
2. **Create Prompt File**: Add instructions in `prompts/new_agent.md`
3. **Register with Orchestrator**: Add to `_init_agents()` in orchestrator
4. **Add to Conversation Flow**: Update conversation flow in `_phase_agent_conversations()`
5. **Test**: Run examples to verify integration

Example agent creation:

```python
# In providers/new_agent.py
from .base_agent import BaseAgent, AgentConfig, AgentRole

class NewAnalysisAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    # Implement required abstract methods
    # Use conversation isolation via parent class
```

## Debugging and Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure both `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` are set
2. **Conversation Isolation Issues**: Check that requests are queued properly in `_process_request_queue()`
3. **Cache Performance**: Monitor cache hit ratios in conversation logs
4. **Agent Communication**: Verify agents are registered with message bus correctly

### Debugging Tools

- **Conversation Logger**: Real-time logging of agent interactions
- **Debug Logs**: Human-readable conversation flow in `debug_logs/`
- **Message History**: Complete message routing history in message bus
- **Agent Stats**: Token usage, costs, and cache performance per conversation

### Performance Optimization

- **Caching**: Enable cache control blocks for Anthropic, context caching for Gemini
- **Batch Sizes**: Tune `stories_per_conversation` in configuration
- **Model Selection**: Use appropriate models (haiku for fast analysis, sonnet for complex tasks)
- **Conversation Reuse**: Leverage conversation context for related analyses

## Architecture Benefits

### Conversation Integrity
- **No Context Contamination**: Each agent pair maintains separate conversation history
- **Sequential Processing**: Request queueing prevents race conditions
- **Isolated Analysis**: Agents can't accidentally influence each other's contexts

### Scalability
- **Native SDK Features**: Direct access to provider-specific optimizations
- **Async Processing**: Full async/await support throughout the system
- **Modular Design**: Easy to add new agents or modify existing ones

### Maintainability
- **External Prompts**: All instructions in version-controlled markdown files
- **Clear Separation**: Distinct responsibilities for discovery, analysis, synthesis
- **Comprehensive Logging**: Detailed conversation and performance tracking

This system provides a robust foundation for multi-perspective news analysis with sophisticated agent coordination, conversation isolation, and efficient resource usage.