# News Intelligence Pipeline V3

A sophisticated AI-powered news intelligence system that discovers, analyzes, and synthesizes news from multiple categories with Greek-focused output.

## Overview

The system uses specialized AI agents to:
1. **Discover** top news stories across 6 categories
2. **Contextualize** with Greek and international perspectives (conditional)
3. **Fact-check** through interrogation-based verification
4. **Synthesize** into comprehensive Greek narratives

### Parallel Architecture

The system uses **per-story agent isolation** (`parallel_category_orchestrator.py`) where each news story gets its own dedicated context and fact-checking agents, ensuring no context contamination between stories.

## Architecture

```
Phase 1: Discovery (Parallel)
├── Greek Political News → 10 stories
├── Greek Economic News → 10 stories
├── International Political → 10 stories
├── International Economic → 10 stories
├── Science News → 10 stories
└── Technology News → 10 stories

Phase 2: Context (Conditional per story)
├── Greek Context Agent → Always active
└── International Context → Only if relevance ≥ 7 or sci/tech

Phase 3: Fact-Check (Interrogation)
├── Identify claims in context
└── Direct agents to verify

Phase 4: Synthesis
└── Greek narrative with all sources
```

## Key Features

- **Parallel Discovery**: 6 category-specific agents running simultaneously
- **Smart Activation**: International context only when adds value (~40% savings)
- **Interrogation Model**: Fact-checker directs searches for better verification
- **Greek Output**: Professional Greek synthesis for target audience

### Key Benefits

- **True Isolation**: Each story gets its own context and fact-check agents
- **No Context Contamination**: Stories analyzed independently
- **Parallel Processing**: Multiple stories processed concurrently
- **Complete Fact-Checking**: Full interrogation → verification → compilation loop
- **Resource Management**: Agents cleaned up after each story
- **Scalability**: Process 60 stories with 60+ isolated agent instances

## Installation

```bash
# Clone repository
git clone <repo-url>
cd agents_v3

# Install dependencies
pip install anthropic google-genai asyncio pyyaml

# Set API keys
export ANTHROPIC_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
```

## Usage

```python
from orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator

# Run daily analysis with per-story agents
orchestrator = ParallelCategoryOrchestrator()
await orchestrator.initialize_agents()
stories = await orchestrator.discover_all_categories("2024-01-30")
results = await orchestrator.process_all_stories()  # Spawns agents per story
```

## Project Structure

```
agents_v3/
├── orchestration/
│   └── category_orchestrator.py    # Main pipeline controller
├── providers/
│   ├── base_agent.py              # Agent base class
│   ├── anthropic_agent.py         # Claude implementation
│   └── gemini_agent.py            # Gemini + Search
├── prompts/
│   ├── discovery_categories.yaml   # Category definitions
│   ├── *_agent.yaml               # Agent-specific prompts
│   └── shared prompts...
├── communication/                  # Inter-agent messaging
├── conversation_logging/           # Logging system
└── utils/                         # Prompt loaders
```

## Testing

```bash
# Test without API keys
python examples/test_category_pipeline.py

# Test system components
python examples/test_system_no_api.py
```

## Configuration

Edit `prompts/discovery_categories.yaml` to:
- Modify news categories
- Update search terms
- Change relevance criteria
- Add/remove sources

## Documentation

- `PIPELINE_ARCHITECTURE.md` - Detailed system design
- `PIPELINE_IMPROVEMENTS_SUMMARY.md` - Recent improvements
- `CLAUDE.md` - AI assistant instructions