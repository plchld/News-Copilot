# News Copilot Prompt Architecture

This document defines the standardized approach for constructing and passing prompts throughout the News Copilot system.

**Last Updated**: May 2025  
**Status**: Fully Implemented

## Core Principles

1. **Separation of Concerns**: System prompts contain instructions; user messages contain content to analyze
2. **Centralized Utilities**: All prompts should use `prompt_utils.py` helpers
3. **Consistent Identity**: Every prompt must include SYSTEM_PREFIX and TRUST_GUARDRAILS
4. **Greek Output**: All prompts request Greek output while being written in English

## Standard Prompt Construction Pattern

```python
from api.prompt_utils import (
    build_prompt,
    inject_runtime_search_context,
    get_[analysis_type]_task_instruction,
    get_[analysis_type]_schema
)

# Step 1: Generate task-specific instruction
task_instruction = get_[analysis_type]_task_instruction(article_text)

# Step 2: Get the appropriate JSON schema
json_schema = get_[analysis_type]_schema()

# Step 3: Build complete prompt with system components
system_prompt = build_prompt(task_instruction, json_schema)

# Step 4: Inject search context for transparency
system_prompt = inject_runtime_search_context(system_prompt, search_params)

# Step 5: Create messages array
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": article_text}
]
```

## Components Breakdown

### SYSTEM_PREFIX (Always Included)
```
You are News-Copilot, an AI news analysis assistant that:
* Works for Greek readers and MUST provide ALL output in Greek language
* MUST process thoughts in a private scratchpad before the final answer
* MUST output ONLY the final answer in Greek after the scratchpad
* If evidence is insufficient, respond with "Άγνωστο" (Unknown) rather than speculating
* ALL final output text MUST be in Greek, including JSON string values
```

### TRUST_GUARDRAILS (Always Included)
```
CRITICAL QUALITY RULES:
1. For every factual claim, mention WHERE you found this information
2. DO NOT invent URLs - just mention the source name/publication
3. If no reliable source is found, explicitly state: "Δεν βρέθηκαν αξιόπιστες πηγές..."
4. DO NOT invent statistics, dates, or quotes
5. Think step-by-step in Greek within ⧼SCRATCHPAD⧽ ... ⧼END_SCRATCHPAD⧽ tags
6. Remember: ALL output text values MUST be in Greek language
7. Citations will be automatically collected from your search
```

### Task Instructions
- Specific to each analysis type
- Written in English
- Request Greek output
- Avoid redundant search instructions

### JSON Schema
- Defines expected output structure
- Field descriptions in Greek
- Enforces data consistency

## Anti-Patterns to Avoid

1. **DON'T** concatenate article text with system prompt
2. **DON'T** include "Use Live Search" instructions (handled by search params)
3. **DON'T** hardcode language instructions multiple times
4. **DON'T** build prompts inline without using utilities
5. **DON'T** truncate article text in prompts

## Agent-Specific Guidelines

### Analysis Agents
- Use simplified prompts for their specific task
- Let base_agent.py handle system components
- Focus on task-specific instructions only

### X-Pulse Sub-Agents
- Should use centralized prompt builders
- Optimize for grok-3-mini where applicable
- Maintain consistency with main agents

## Search Parameter Integration

Search parameters are configured separately and include:
- Domain exclusion (current article)
- Language preferences
- Source types
- Result limits

The `inject_runtime_search_context()` function adds transparency about active search parameters.

## Migration Checklist

When updating existing code:
- [ ] Remove direct prompt concatenation
- [ ] Import appropriate prompt_utils functions
- [ ] Use get_[type]_task_instruction() 
- [ ] Use get_[type]_schema()
- [ ] Apply build_prompt() for system components
- [ ] Add inject_runtime_search_context()
- [ ] Ensure article text goes in user message
- [ ] Remove redundant language instructions
- [ ] Test Greek output consistency

## Example: Properly Constructed Agent

```python
class OptimizedAgent(AnalysisAgent):
    @staticmethod
    def _build_prompt(context: Dict[str, Any]) -> str:
        # Use task instruction from prompt_utils
        from ..prompt_utils import get_[analysis_type]_task_instruction
        article_text = context.get('article_text', '')
        return get_[analysis_type]_task_instruction(article_text)
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        # Use centralized search param builder
        from ..search_params_builder import get_search_params_for_[analysis_type]
        from urllib.parse import urlparse
        
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_[analysis_type](mode="on", article_domain=article_domain)
```

The base_agent will automatically wrap this with SYSTEM_PREFIX and TRUST_GUARDRAILS.

## Conversation-Based Refinement

The system supports iterative refinement using xAI's conversation capability:

```python
# In coordinator_v2.py
conversation_history = [
    {
        "role": "assistant",
        "content": json.dumps(initial_result.data, ensure_ascii=False)
    },
    {
        "role": "user", 
        "content": quality_result.refinement_prompt
    }
]

refinement_context = {
    **context,
    'conversation_history': conversation_history,
    'is_refinement': True
}
```

This allows the coordinator to ask agents to improve their responses based on quality checks.

## Implementation Status

### ✅ Fully Updated Agents
- **JargonAgent**: Uses `get_jargon_task_instruction()` and proper search params
- **ViewpointsAgent**: Uses `get_alt_view_task_instruction()` and proper search params  
- **FactCheckAgent**: Uses `get_fact_check_task_instruction()` and proper search params
- **BiasAnalysisAgent**: Uses `get_bias_analysis_task_instruction()` and proper search params
- **TimelineAgent**: Uses `get_timeline_task_instruction()` and proper search params
- **ExpertOpinionsAgent**: Uses `get_expert_opinions_task_instruction()` and proper search params

### ✅ Infrastructure Updates
- **base_agent.py**: Automatically adds SYSTEM_PREFIX and TRUST_GUARDRAILS
- **analysis_handlers.py**: Uses prompt_utils for all augmentations
- **coordinator_v2.py**: Supports conversation-based refinement

### ⚠️ Pending Updates
- **X-Pulse sub-agents**: Still use inline prompts (but functional)

## Quality Assurance

All prompts now:
1. Include News-Copilot identity and Greek output requirements
2. Use scratchpad technique for reasoning
3. Have proper search parameter configuration with domain exclusion
4. Support conversation-based refinement for quality improvement