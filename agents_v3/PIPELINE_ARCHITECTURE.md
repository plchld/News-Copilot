# News Intelligence Pipeline Architecture V2

## Overview

The pipeline operates in distinct phases with conditional agent activation based on content analysis. Each news category has its own discovery agent, and downstream agents are activated only when needed.

## Pipeline Flow

### Phase 1: Category-Based Discovery (Parallel)
- **Greek Political News Discovery** → 10 stories
- **Greek Economic News Discovery** → 10 stories  
- **International Political News Discovery** → 10 stories
- **International Economic News Discovery** → 10 stories
- **Science News Discovery** → 10 stories
- **Technology News Discovery** → 10 stories

### Phase 2: Context Enrichment (Conditional)
For each discovered story:

#### Greek News Processing:
1. **Assess International Relevance** (built into discovery agent)
   - If HIGH international relevance → Activate **International Context Agent**
   - If LOW international relevance → Activate **Greek Context Agent** only

#### International News Processing:
- Always activate **Greek Context Agent** to find Greek perspectives

#### Science/Tech News Processing:
- Activate both **Greek Context Agent** and **International Context Agent**

### Phase 3: Fact-Checking (Interrogation-Based)
- **Fact-Check Interrogator Agent**:
  - Identifies claims in upstream agent responses
  - Interrogates context agents to perform searches
  - Compiles fact-check results with citations
  - Does NOT perform searches itself

### Phase 4: Synthesis (Greek Output)
- **Greek Synthesis Agent**:
  - Queries all activated context agents
  - Retrieves fact-check results
  - Creates comprehensive Greek narrative
  - Includes all sources and fact-checks

## Agent Definitions

### Discovery Agents (6 total)
- Specialized by category
- Find top 10 stories daily
- Assess international relevance for Greek stories
- Use Google Search via Gemini

### Context Agents (2 types)
- **Greek Context Agent**: Finds alternative Greek viewpoints
- **International Context Agent**: Finds international perspectives

### Fact-Check Interrogator (1)
- Analyzes claims in context agent outputs
- Formulates fact-check queries
- Directs context agents to search
- Compiles results

### Synthesis Agent (1)
- Creates final Greek narrative
- Integrates all perspectives
- Includes fact-check results
- Optimized for Greek readers

## Key Improvements

1. **Parallel Discovery**: All categories discovered simultaneously
2. **Conditional Activation**: Agents only run when needed
3. **Interrogation Model**: Fact-checker directs searches instead of searching
4. **Greek-First Output**: Final synthesis in Greek for target audience
5. **Efficient Context**: International context only when adds value