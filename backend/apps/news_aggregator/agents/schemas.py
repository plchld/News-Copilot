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
                "description": "Comprehensive synthesis of different viewpoints found through search, in Greek."
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
                            "enum": ["ισχυρά τεκμηριωμένο", "μερικώς τεκμηριωμένο", "αμφιλεγόμενο", 
                                    "ελλιπώς τεκμηριωμένο", "χωρίς επαρκή στοιχεία", "εκτός πλαισίου"],
                            "description": "Assessment of evidence quality"
                        },
                        "context": {"type": "string", "description": "Detailed explanation in Greek"},
                        "complexity_note": {"type": "string", "description": "Additional context if needed"},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relevant sources found"
                        }
                    },
                    "required": ["claim", "evidence_assessment", "context"]
                }
            }
        },
        "required": ["claims"]
    }

# Bias Agent Schema
def get_bias_response_schema() -> Dict[str, Any]:
    """Schema for bias agent responses"""
    return {
        "type": "object",
        "properties": {
            "political_leaning": {
                "type": "string",
                "enum": ["Αριστερά", "Κεντροαριστερά", "Κέντρο", "Κεντροδεξιά", "Δεξιά", "Ουδέτερο"],
                "description": "Political orientation assessment"
            },
            "bias_indicators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific bias indicators found"
            },
            "language_analysis": {
                "type": "string",
                "description": "Analysis of language used"
            },
            "framing_analysis": {
                "type": "string", 
                "description": "How issues are framed"
            },
            "balance_assessment": {
                "type": "string",
                "description": "Assessment of overall balance"
            }
        },
        "required": ["political_leaning", "bias_indicators", "language_analysis"]
    }

# Timeline Agent Schema
def get_timeline_response_schema() -> Dict[str, Any]:
    """Schema for timeline agent responses"""
    return {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date or time period"},
                        "event": {"type": "string", "description": "Event description in Greek"},
                        "significance": {"type": "string", "description": "Why this event matters"},
                        "context": {"type": "string", "description": "Additional context"}
                    },
                    "required": ["date", "event", "significance"]
                }
            }
        },
        "required": ["events"]
    }

# Expert Agent Schema
def get_expert_response_schema() -> Dict[str, Any]:
    """Schema for expert agent responses"""
    return {
        "type": "object",
        "properties": {
            "topic_domain": {
                "type": "string",
                "description": "Main domain of expertise needed"
            },
            "expert_perspectives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "description": "Field of expertise"},
                        "perspective": {"type": "string", "description": "Expert viewpoint in Greek"},
                        "key_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main points from this perspective"
                        }
                    },
                    "required": ["field", "perspective"]
                }
            },
            "consensus_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Points of expert consensus"
            },
            "debate_points": {
                "type": "array", 
                "items": {"type": "string"},
                "description": "Points of expert debate"
            }
        },
        "required": ["expert_perspectives"]
    }

# X Pulse Agent Schemas
def get_sentiment_schema() -> Dict[str, Any]:
    """Schema for sentiment analysis sub-agent"""
    return {
        "type": "object",
        "properties": {
            "overall_sentiment": {
                "type": "string",
                "enum": ["πολύ θετικό", "θετικό", "ουδέτερο", "αρνητικό", "πολύ αρνητικό", "μικτό"],
                "description": "Overall sentiment assessment"
            },
            "sentiment_breakdown": {
                "type": "object",
                "properties": {
                    "positive": {"type": "number", "minimum": 0, "maximum": 100},
                    "negative": {"type": "number", "minimum": 0, "maximum": 100},
                    "neutral": {"type": "number", "minimum": 0, "maximum": 100}
                }
            },
            "key_emotions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main emotions expressed"
            }
        },
        "required": ["overall_sentiment", "sentiment_breakdown"]
    }

# Pydantic models for type safety
class JargonTerm(BaseModel):
    term: str
    explanation: str
    context: Optional[str] = None
    source_mention: Optional[str] = None

class JargonResponse(BaseModel):
    terms: List[JargonTerm]

class ViewpointSource(BaseModel):
    source: str
    perspective_summary: str

class ViewpointResponse(BaseModel):
    topic_analysis: Optional[str] = None
    alternative_perspectives: str
    key_sources: List[ViewpointSource] = []

class FactCheckClaim(BaseModel):
    claim: str
    evidence_assessment: str
    context: str
    complexity_note: Optional[str] = None
    sources: List[str] = []

class FactCheckResponse(BaseModel):
    claims: List[FactCheckClaim]

class BiasResponse(BaseModel):
    political_leaning: str
    bias_indicators: List[str]
    language_analysis: str
    framing_analysis: Optional[str] = None
    balance_assessment: Optional[str] = None

class TimelineEvent(BaseModel):
    date: str
    event: str
    significance: str
    context: Optional[str] = None

class TimelineResponse(BaseModel):
    events: List[TimelineEvent]

class ExpertPerspective(BaseModel):
    field: str
    perspective: str
    key_points: List[str] = []

class ExpertResponse(BaseModel):
    topic_domain: Optional[str] = None
    expert_perspectives: List[ExpertPerspective]
    consensus_points: List[str] = []
    debate_points: List[str] = []

class SentimentResponse(BaseModel):
    overall_sentiment: str
    sentiment_breakdown: Dict[str, float]
    key_emotions: List[str] = []