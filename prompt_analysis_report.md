# News Copilot Prompt Architecture Analysis Report

## Executive Summary

This analysis examines the prompt structure, consistency, and quality across the News Copilot agentic architecture. The system demonstrates a well-architected prompt engineering approach with centralized utilities, but reveals several areas for improvement regarding consistency, prompt optimization, and adherence to best practices.

## 1. Prompt Architecture Overview

### 1.1 Centralized Components
The system uses `api/prompt_utils.py` as the central hub for prompt engineering, providing:

- **SYSTEM_PREFIX**: Establishes News-Copilot identity and Greek language requirements
- **TRUST_GUARDRAILS**: Implements quality controls and citation requirements
- **JSON_ENVELOPE**: Standardizes JSON output formatting
- **Schema Definitions**: Comprehensive schemas for each analysis type
- **Task Instruction Generators**: Functions for building task-specific prompts
- **Self-Critique Template**: For response validation

### 1.2 Prompt Construction Flow
1. Base prompt created via `build_prompt()` combining system prefix + guardrails + task instructions
2. Runtime search context injection via `inject_runtime_search_context()`
3. JSON schema appended when structured output needed
4. Article text passed separately in user message role

## 2. Consistency Analysis

### 2.1 ✅ Consistent Elements
- All agents correctly use Greek language requirements
- JSON schema definitions are well-structured and comprehensive
- Search parameter handling is centralized and consistent
- All agents properly exclude the source article domain from searches

### 2.2 ❌ Inconsistencies Identified

#### A. Prompt Utility Usage
- **JargonAgent**: Uses minimal custom prompt, NOT using `prompt_utils` functions
- **ViewpointsAgent**: Has its own `GROK_ALTERNATIVE_VIEWPOINTS_PROMPT` constant, bypassing prompt utilities
- **FactCheckAgent**: Uses minimal custom prompt without prompt utilities
- **BiasAnalysisAgent**: Uses minimal custom prompt without prompt utilities
- **TimelineAgent** & **ExpertOpinionsAgent**: ✅ Properly use prompt_utils functions

#### B. Scratchpad Technique
- The scratchpad technique is defined in `TRUST_GUARDRAILS` but:
  - NOT used by any agent prompts
  - The `⧼SCRATCHPAD⧽...⧼END_SCRATCHPAD⧽` pattern is never implemented
  - This represents a significant gap between design and implementation

#### C. System Prefix Integration
- ViewpointsAgent uses a completely custom prompt that doesn't include SYSTEM_PREFIX
- Other agents rely on base_agent.py to add system components, creating indirect dependencies

## 3. Prompt Quality Assessment

### 3.1 Strengths
1. **Clear Greek Language Requirements**: All prompts emphasize Greek output
2. **Structured Output**: Well-defined JSON schemas prevent ambiguity
3. **Source Attribution**: Good emphasis on citing sources and avoiding fabrication
4. **Comprehensive Schemas**: Detailed field descriptions in Greek
5. **Search Context Transparency**: Proper handling of excluded sites with transparency notices

### 3.2 Weaknesses

#### A. Overly Brief Agent Prompts
Most agents use extremely minimal prompts:
```python
# JargonAgent
"""Identify technical terms, organizations, and historical references that need explanation.
Provide brief explanations (1-2 sentences) in GREEK for each term."""

# FactCheckAgent  
"""Verify the main claims, statistics, dates, and events in the article.
Focus on the 3-5 most important claims.
ALL explanations and warnings must be in GREEK."""
```

These lack:
- Context about News-Copilot's role
- Detailed instructions for quality output
- Examples of expected behavior
- The scratchpad reasoning technique

#### B. Missing Prompt Engineering Best Practices
1. **No Few-Shot Examples**: No agents provide examples of good output
2. **No Chain-of-Thought**: Despite scratchpad being defined, it's not used
3. **Limited Context**: Minimal background on the analysis purpose
4. **No Error Handling Instructions**: What to do when information is unclear

#### C. Inconsistent Integration with Base Infrastructure
- Some agents build prompts assuming base_agent will add system components
- Others (ViewpointsAgent) include everything in their custom prompt
- This creates maintenance challenges and potential for errors

## 4. Search Parameter Handling

### 4.1 ✅ Well-Implemented Features
- Centralized `search_params_builder.py` with sensible defaults
- Proper article domain exclusion across all agents
- International topic detection for multilingual search
- Transparency about excluded sites
- Appropriate source selection per analysis type

### 4.2 Areas for Improvement
- BiasAnalysisAgent returns None for search params (correct, but could be documented why)
- X Pulse sub-agents have custom search param logic that could be centralized

## 5. Greek Language Implementation

### 5.1 ✅ Strengths
- Consistent Greek output requirements across all prompts
- Greek enum values in schemas (e.g., "υψηλή", "μέτρια", "χαμηλή")
- Greek field descriptions in schemas
- Proper Unicode handling

### 5.2 ❌ Issues
- Some error messages and internal strings remain in English
- Mixed Greek/English in some prompt instructions
- ViewpointsAgent prompt has English-heavy instructions

## 6. Specific Agent Analysis

### 6.1 High-Quality Implementation
- **TimelineAgent**: Properly uses `get_timeline_task_instruction()`
- **ExpertOpinionsAgent**: Properly uses `get_expert_opinions_task_instruction()`

### 6.2 Needs Improvement
- **JargonAgent**: Should use `get_jargon_task_instruction()` from prompt_utils
- **ViewpointsAgent**: Should use `get_alt_view_task_instruction()` 
- **FactCheckAgent**: Should use `get_fact_check_task_instruction()`
- **BiasAnalysisAgent**: Should use `get_bias_analysis_task_instruction()`

### 6.3 Complex Cases
- **XPulseAgent**: Uses nested sub-agents with custom prompts - acceptable given complexity
- **CollaborativeAgents**: Experimental system with unique requirements

## 7. Recommendations

### 7.1 Immediate Actions
1. **Standardize All Agents on prompt_utils**:
   - Modify JargonAgent to use `get_jargon_task_instruction()`
   - Modify ViewpointsAgent to use `get_alt_view_task_instruction()`
   - Modify FactCheckAgent to use `get_fact_check_task_instruction()`
   - Modify BiasAnalysisAgent to use `get_bias_analysis_task_instruction()`

2. **Implement Scratchpad Technique**:
   - Add scratchpad usage to all task instruction generators
   - Update agents to properly handle scratchpad in responses
   - Add examples showing proper scratchpad usage

3. **Enhance Prompt Quality**:
   - Add few-shot examples to each task instruction
   - Include more detailed quality criteria
   - Add error handling instructions

### 7.2 Medium-Term Improvements
1. **Create Prompt Testing Framework**:
   - Unit tests for prompt generation
   - Validation of prompt/schema alignment
   - Response quality benchmarks

2. **Develop Prompt Templates**:
   - Reusable components for common patterns
   - Standardized error handling blocks
   - Consistent formatting guidelines

3. **Implement Prompt Versioning**:
   - Track prompt changes over time
   - A/B testing capability for prompt improvements
   - Rollback mechanism for problematic changes

### 7.3 Long-Term Vision
1. **Dynamic Prompt Optimization**:
   - Learn from successful/failed analyses
   - Adjust prompts based on user feedback
   - Model-specific prompt variants

2. **Multilingual Prompt System**:
   - Extend beyond Greek to other languages
   - Maintain quality across translations
   - Cultural adaptation of prompts

## 8. Code Quality Metrics

### Prompt Consistency Score: 6/10
- Centralized utilities exist but underutilized
- Inconsistent implementation across agents
- Missing key features (scratchpad)

### Prompt Completeness: 7/10
- Good schemas and structure
- Missing examples and detailed instructions
- Limited error handling guidance

### Greek Language Integration: 9/10
- Excellent Greek requirements throughout
- Minor English remnants in edge cases
- Proper Unicode support

### Search Integration: 8/10
- Well-designed parameter builder
- Good transparency features
- Minor customization inefficiencies

## 9. Conclusion

The News Copilot prompt architecture demonstrates solid foundational design with centralized utilities and comprehensive schemas. However, implementation inconsistencies and underutilization of advanced prompt engineering techniques limit its effectiveness. By standardizing all agents on the prompt_utils functions and implementing the planned scratchpad technique, the system can achieve significantly better consistency and quality in its AI-powered analyses.

The immediate priority should be updating the four agents that don't use prompt_utils to maintain architectural consistency and enable easier maintenance and improvements across the entire system.