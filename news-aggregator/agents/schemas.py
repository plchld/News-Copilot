"""
Structured output schemas for News Copilot agents
Ensures consistent data structures between backend and frontend
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Jargon Agent Schema
def get_jargon_response_schema() -> Dict[str, Any]:
    """Schema for jargon agent responses"""
    return {
        "type": "object",
        "properties": {
            "terms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "The technical term"},
                        "explanation": {"type": "string", "description": "Clear explanation in Greek"},
                        "context": {"type": "string", "description": "Context from the article"},
                        "source_mention": {"type": "string", "description": "Source where term was found"}
                    },
                    "required": ["term", "explanation"]
                }
            }
        },
        "required": ["terms"]
    }

# Viewpoints Agent Schema  
def get_viewpoints_response_schema() -> Dict[str, Any]:
    """Schema for viewpoints agent responses"""
    return {
        "type": "object",
        "properties": {
            "topic_analysis": {
                "type": "string", 
                "description": "Brief analysis of the main topic in Greek"
            },
            "alternative_perspectives": {
                "type": "string",
                "description": "Comprehensive synthesis of different viewpoints found through search, in Greek. Can be structured as paragraphs or sections as needed for clarity."
            },
            "key_sources": {
                "type": "array",
                "items": {
                    "type": "object", 
                    "properties": {
                        "source": {"type": "string"},
                        "perspective_summary": {"type": "string", "description": "Brief summary in Greek"}
                    }
                },
                "description": "Main sources consulted"
            }
        },
        "required": ["alternative_perspectives"]
    }

# Fact Check Agent Schema
def get_fact_check_response_schema() -> Dict[str, Any]:
    """Schema for fact check agent responses"""
    return {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string", "description": "The specific claim being checked"},
                        "evidence_assessment": {
                            "type": "string", 
                            "enum": ["ισχυρά τεκμηριωμένο", "μερικώς τεκμηριωμένο", "αμφιλεγόμενο", "ελλιπώς τεκμηριωμένο", "χωρίς επαρκή στοιχεία", "εκτός πλαισίου"],
                            "description": "Assessment of evidence quality"
                        },
                        "context": {"type": "string", "description": "Detailed explanation in Greek"},
                        "complexity_note": {"type": "string", "description": "Additional context if needed"},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of sources used for verification"
                        }
                    },
                    "required": ["claim", "evidence_assessment", "context"]
                }
            },
            "source_quality": {
                "type": "object",
                "properties": {
                    "primary_sources": {"type": "integer"},
                    "secondary_sources": {"type": "integer"},
                    "source_diversity": {"type": "string"}
                }
            }
        },
        "required": ["claims"]
    }

# Bias Analysis Agent Schema
def get_bias_analysis_response_schema() -> Dict[str, Any]:
    """Schema for bias analysis agent responses"""
    return {
        "type": "object",
        "properties": {
            "political_spectrum_analysis_greek": {
                "type": "object",
                "properties": {
                    "economic_axis_placement": {"type": "string"},
                    "economic_axis_justification": {"type": "string"},
                    "social_axis_placement": {"type": "string"},
                    "social_axis_justification": {"type": "string"},
                    "overall_confidence": {"type": "string"}
                }
            },
            "language_and_framing_analysis": {
                "type": "object",
                "properties": {
                    "emotionally_charged_terms": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "term": {"type": "string"},
                                "explanation": {"type": "string"}
                            }
                        }
                    },
                    "identified_framing_techniques": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "technique_name": {"type": "string"},
                                "example_from_article": {"type": "string"}
                            }
                        }
                    },
                    "detected_tone": {"type": "string"},
                    "missing_perspectives_summary": {"type": "string"}
                }
            },
            "sources_diversity": {"type": "string"},
            "analysis_summary": {"type": "string"},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["political_spectrum_analysis_greek", "language_and_framing_analysis"]
    }

# Timeline Agent Schema
def get_timeline_response_schema() -> Dict[str, Any]:
    """Schema for timeline agent responses"""
    return {
        "type": "object",
        "properties": {
            "story_title": {"type": "string"},
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "importance": {"type": "string"},
                        "source": {"type": "string"}
                    },
                    "required": ["date", "title", "description"]
                }
            },
            "context": {"type": "string"},
            "future_implications": {"type": "string"}
        },
        "required": ["events"]
    }

# Expert Opinions Agent Schema
def get_expert_opinions_response_schema() -> Dict[str, Any]:
    """Schema for expert opinions agent responses"""
    return {
        "type": "object",
        "properties": {
            "topic_summary": {"type": "string"},
            "experts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "credentials": {"type": "string"},
                        "opinion": {"type": "string"},
                        "quote": {"type": "string"},
                        "source": {"type": "string"},
                        "source_url": {"type": "string"},
                        "stance": {"type": "string"}
                    },
                    "required": ["name", "opinion"]
                }
            },
            "consensus": {"type": "string"},
            "key_debates": {"type": "string"}
        },
        "required": ["experts"]
    }

# X Pulse Agent Schema
def get_x_pulse_response_schema() -> Dict[str, Any]:
    """Schema for X pulse agent responses"""
    return {
        "type": "object",
        "properties": {
            "overall_discourse_summary": {"type": "string"},
            "discussion_themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "theme_title": {"type": "string"},
                        "theme_summary": {"type": "string"},
                        "representative_posts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "post_content": {"type": "string"},
                                    "post_source_description": {"type": "string"}
                                }
                            }
                        },
                        "sentiment_around_theme": {"type": "string"}
                    },
                    "required": ["theme_title", "theme_summary"]
                }
            },
            "data_caveats": {"type": "string"}
        },
        "required": ["discussion_themes"]
    }

# Schema mapping for easy access
AGENT_SCHEMAS = {
    'jargon': get_jargon_response_schema,
    'viewpoints': get_viewpoints_response_schema,
    'fact-check': get_fact_check_response_schema,
    'bias': get_bias_analysis_response_schema,
    'timeline': get_timeline_response_schema,
    'expert': get_expert_opinions_response_schema,
    'x-pulse': get_x_pulse_response_schema
}

def get_schema_for_agent(agent_type: str) -> Dict[str, Any]:
    """Get schema for a specific agent type"""
    if agent_type in AGENT_SCHEMAS:
        return AGENT_SCHEMAS[agent_type]()
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")