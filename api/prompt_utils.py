# api/prompt_utils.py
"""
Prompt engineering utilities for hardened, reliable Grok responses.
Implements scratchpad technique and strict citation requirements.
"""

import json
from typing import Dict, Optional, Any

# System-level instructions for all prompts
SYSTEM_PREFIX = """
You are News-Copilot, an AI news analysis assistant that:
* Works for Greek readers and MUST provide ALL output in Greek language
* MUST process thoughts in a private scratchpad before the final answer
* MUST output ONLY the final answer in Greek after the scratchpad
* If evidence is insufficient, respond with "Άγνωστο" (Unknown) rather than speculating
* ALL final output text MUST be in Greek, including JSON string values
"""

# Trust and quality guardrails
TRUST_GUARDRAILS = """
CRITICAL QUALITY RULES:
1. For every factual claim, mention WHERE you found this information (e.g., "according to Kathimerini", "as reported by SKAI")
2. DO NOT invent URLs - just mention the source name/publication
3. If no reliable source is found, explicitly state: "Δεν βρέθηκαν αξιόπιστες πηγές για αυτήν την πληροφορία."
4. DO NOT invent statistics, dates, or quotes
5. Think step-by-step in Greek within ⧼SCRATCHPAD⧽ ... ⧼END_SCRATCHPAD⧽ tags
   - Delete the scratchpad before the final answer
   - The user-facing answer starts after the label: ### ΑΠΟΤΕΛΕΣΜΑΤΑ ###
6. Remember: ALL output text values MUST be in Greek language
7. Citations will be automatically collected from your search - focus on mentioning sources naturally in your text
"""


def get_jargon_response_schema() -> dict:
    """
    Get JSON schema for jargon/term explanations.
    Aligns with api.models.JargonResponse
    """
    return {
        "type": "object",
        "properties": {
            "terms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string"},
                        "explanation": {"type": "string"},
                        "source_mention": {"type": "string"}  # Where info came from
                    },
                    "required": ["term", "explanation"]
                }
            }
        },
        "required": ["terms"]
    }


def get_alternative_viewpoints_schema() -> dict:
    """
    Get JSON schema for alternative viewpoints response.
    """
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "source_title": {"type": "string"},
                "provider": {"type": "string"}, 
                "published_date": {"type": "string"},
                "difference_summary": {"type": "string"}
            },
            "required": ["source_title", "provider", "difference_summary"]
        }
    }


def get_fact_check_schema() -> dict:
    """
    Get JSON schema for fact-checking response.
    """
    return {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "evidence_assessment": {
                            "type": "string",
                            "enum": [
                                "ισχυρά τεκμηριωμένο",      # strongly supported
                                "μερικώς τεκμηριωμένο",     # partially supported
                                "αμφιλεγόμενο",             # disputed/contested
                                "ελλιπώς τεκμηριωμένο",     # poorly supported
                                "χωρίς επαρκή στοιχεία",    # insufficient evidence
                                "εκτός πλαισίου"            # out of context
                            ]
                        },
                        "context": {"type": "string"},  # Important context/nuance
                        "complexity_note": {"type": "string"},  # Why this is complex
                        "sources": {
                            "type": "array",
                            "items": {"type": "string", "format": "url"},
                            "minItems": 1
                        }
                    },
                    "required": ["claim", "evidence_assessment", "context", "sources"]
                }
            },
            "source_quality": {
                "type": "object",
                "properties": {
                    "primary_sources": {"type": "integer", "minimum": 0},
                    "secondary_sources": {"type": "integer", "minimum": 0},
                    "source_diversity": {
                        "type": "string",
                        "enum": ["πολύ ποικίλες", "μέτρια ποικιλία", "περιορισμένες", "μονομερείς"]
                    }
                },
                "required": ["primary_sources", "secondary_sources", "source_diversity"]
            }
        },
        "required": ["claims", "source_quality"]
    }


def get_bias_analysis_schema() -> dict:
    """
    Get JSON schema for bias analysis response.
    """
    return {
        "type": "object",
        "properties": {
            "political_lean": {
                "type": "string",
                "enum": ["αριστερά", "κεντροαριστερά", "κέντρο", "κεντροδεξιά", "δεξιά", "ουδέτερο", "άγνωστο"]
            },
            "tone": {
                "type": "string",
                "enum": ["θετικό", "αρνητικό", "ουδέτερο", "μικτό"]
            },
            "framing_techniques": {
                "type": "array",
                "items": {"type": "string"}
            },
            "emotional_language": {
                "type": "array",
                "items": {"type": "string"}
            },
            "sources_diversity": {
                "type": "string",
                "enum": ["υψηλή", "μέτρια", "χαμηλή", "μονομερής"]
            },
            "analysis_summary": {"type": "string"},
            "supporting_evidence": {
                "type": "array",
                "items": {"type": "string", "format": "url"}
            }
        },
        "required": ["political_lean", "tone", "framing_techniques", "emotional_language", 
                     "sources_diversity", "analysis_summary", "supporting_evidence"]
    }


def get_timeline_schema() -> dict:
    """
    Get JSON schema for timeline response.
    """
    return {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "event": {"type": "string"},
                        "significance": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string", "format": "url"},
                            "minItems": 1
                        }
                    },
                    "required": ["date", "event", "significance", "sources"]
                }
            }
        },
        "required": ["events"]
    }


def get_expert_opinions_schema() -> dict:
    """
    Get JSON schema for expert opinions response.
    """
    return {
        "type": "object",
        "properties": {
            "opinions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "expert_name": {"type": "string"},
                        "expert_title": {"type": "string"},
                        "opinion": {"type": "string"},
                        "date": {"type": "string"},
                        "source_url": {"type": "string", "format": "url"}
                    },
                    "required": ["expert_name", "expert_title", "opinion", "source_url"]
                }
            }
        },
        "required": ["opinions"]
    }


def JSON_ENVELOPE(schema_obj: dict) -> str:
    """
    Create JSON output instructions with schema.
    
    Args:
        schema_obj: The JSON schema object
    
    Returns:
        String with formatted JSON output instructions
    """
    return f"""### ΑΠΟΤΕΛΕΣΜΑΤΑ ###

Please provide the answer exclusively as JSON that exactly matches the following schema.
Remember: ALL text values in the JSON MUST be in Greek language.
```json
{json.dumps(schema_obj, ensure_ascii=False, indent=2)}
```
Do not include markdown fences around the JSON. No additional fields (keys) are allowed in the JSON.
ALL string values MUST be in Greek."""


def build_prompt(task_instruction: str, json_schema_definition: Optional[dict] = None) -> str:
    """
    Build a complete prompt with system prefix, guardrails, and task instructions.
    
    Args:
        task_instruction: The specific task instructions
        json_schema_definition: Optional JSON schema for structured output
    
    Returns:
        Complete prompt string
    """
    prompt_parts = [SYSTEM_PREFIX, TRUST_GUARDRAILS, task_instruction]
    
    if json_schema_definition:
        prompt_parts.append(JSON_ENVELOPE(json_schema_definition))
    
    return "\n\n".join(prompt_parts)


def inject_runtime_search_context(prompt: str, search_params: dict) -> str:
    """
    Inject search parameters context into the prompt.
    
    Args:
        prompt: The base prompt
        search_params: The search parameters being used
    
    Returns:
        Prompt with search context injected
    """
    if not search_params:
        return prompt
    
    # Filter out None values
    contextual_params = {k: v for k, v in search_params.items() if v is not None}
    if not contextual_params:
        return prompt

    pretty_params = json.dumps(contextual_params, ensure_ascii=False, indent=2)
    context_section = f"""
### Active Search Parameters (Live Search) Context ###
```json
{pretty_params}
```
Use these parameters to guide your search strategy."""
    
    return f"{prompt}{context_section}"


# Task instruction generators

def get_jargon_task_instruction(article_text: str) -> str:
    """Generate task instruction for jargon/term explanations."""
    return f"""Identify ONLY the non-obvious technical terms, organizations, or historical references from the article below.
For each term, provide a clear explanation of 1-2 sentences in Greek.
For each explanation, you MUST provide at least one source (URL) that supports it in the "sources" field.
The final result MUST be a JSON object. Remember: ALL text values must be in Greek.

Article to analyze:
{article_text}"""


def get_alt_view_task_instruction(article_text: str) -> str:
    """Generate task instruction for alternative viewpoints."""
    return f"""Find 4 to 8 reliable sources (preferably Greek) that cover the same news story as the original article.
IMPORTANT: Search primarily in Greek language and prioritize Greek news sources.
For each source, briefly describe (in 1-3 sentences) how its coverage differs from or adds to the original story.
Mention new facts, different perspectives, missing details, or conflicting statements.
Required fields for each source are: "source_title", "provider", "published_date", "difference_summary", and "url".
The final result MUST be a JSON array. Remember: ALL text values must be in Greek.

Original Article:
{article_text}"""


def get_fact_check_task_instruction(article_text: str) -> str:
    """Generate task instruction for fact-checking."""
    return f"""Identify the main claims in the article below and assess their evidence base.
For each claim:
- Assess the strength of available evidence (evidence_assessment)
- Provide important context that may affect interpretation (context)
- Explain why the topic might be complex or nuanced (complexity_note) - optional field
- Provide at least one reliable source

We avoid absolute "true/false" judgments because most topics have multiple dimensions.
Instead, we focus on the quality of evidence and context.

Also assess the source quality of the article (primary sources, secondary sources, diversity).
IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Article to check:
{article_text}"""


def get_bias_analysis_task_instruction(article_text: str) -> str:
    """Generate task instruction for bias analysis."""
    return f"""Analyze the article below for political bias and framing techniques.
Identify:
- Political lean (left, center, right, etc.)
- Emotional tone (positive, negative, neutral)
- Framing techniques used
- Emotionally charged language
- Source diversity
Provide specific examples and URLs that support your analysis.
IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Article to analyze:
{article_text}"""


def get_timeline_task_instruction(article_text: str) -> str:
    """Generate task instruction for timeline construction."""
    return f"""Create a chronological timeline of events related to the topic of the article below.
Include:
- Date of each event
- Description of the event
- Significance/impact of the event
- At least one source (URL) for each event
Focus on the last 30 days unless the topic requires a longer timeframe.
IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Reference article:
{article_text}"""


def get_expert_opinions_task_instruction(article_text: str) -> str:
    """Generate task instruction for expert opinions collection."""
    return f"""Find REAL expert opinions about the topic of the article below.

STRICT REQUIREMENTS:
1. ONLY include experts that you actually find through Live Search
2. DO NOT invent or imagine experts - if you can't find any, return empty array
3. Each expert MUST have been found in your search results
4. The opinion MUST come from actual search results, not speculation
5. If citing X/Twitter, the handle must exist in search results

Search for ACTUAL statements from:
- Greek academics, researchers, analysts who commented on this topic
- Government officials who made statements about this
- Industry experts or organization representatives
- Journalists or commentators with expertise

For each expert found:
- Name must be from search results
- Opinion must be what they actually said (not interpretation)
- Only include if you found them discussing THIS specific topic

IMPORTANT: 
- Search primarily in Greek language
- If no experts found, return empty experts array
- Better to have fewer real experts than many hallucinated ones
- ALL text values in JSON must be in Greek

Reference article:
{article_text}"""


# Self-critique template
def get_self_critique_prompt(schema_str: str, json_to_check_str: str) -> str:
    """
    Generate a self-critique prompt to validate JSON responses.
    
    Args:
        schema_str: The expected schema as a string
        json_to_check_str: The JSON response to validate as a string
    
    Returns:
        Complete critique prompt
    """
    critique_instruction = f"""Check the JSON object below against these rules:
1. Schema Compliance: Is the JSON 100% compatible with the schema below? Check types, required fields, enums.
   Schema: ```json
   {schema_str}
   ```
2. Source Quality: Does each object requiring sources contain at least one valid URL in the "sources" field? (If the schema requires sources).
3. Reliability Rules: Are there violations of CRITICAL QUALITY RULES (e.g., claims without sources, fabrications)?
4. Language Check: Are ALL text values in Greek as required?

If everything is correct, respond ONLY with the word "OK".
Otherwise, provide a brief list of problems found and suggested fixes, in Greek.

JSON to check:
```json
{json_to_check_str}
```"""
    
    return build_prompt(critique_instruction)