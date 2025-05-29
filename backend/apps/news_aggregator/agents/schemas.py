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


class TimelineEvent(BaseModel):
    date: str
    event: str
    significance: str
    context: Optional[str] = None

class TimelineResponse(BaseModel):
    events: List[TimelineEvent]


class SentimentResponse(BaseModel):
    overall_sentiment: str
    sentiment_breakdown: Dict[str, float]
    key_emotions: List[str] = []