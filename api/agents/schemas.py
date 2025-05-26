from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

# Base classes for common patterns
class GreekContent(BaseModel):
    """Base class ensuring Greek content"""
    
    @validator('*', pre=False)
    def ensure_greek(cls, v):
        if isinstance(v, str) and v:
            # Could add Greek character validation here
            pass
        return v

# Jargon Analysis Schema
class JargonTerm(BaseModel):
    term: str = Field(description="Technical term or jargon in original form")
    explanation: str = Field(description="Simple explanation in Greek", min_length=10)
    category: Optional[str] = Field(None, description="Category: τεχνικός, πολιτικός, οικονομικός")

class JargonAnalysis(GreekContent):
    terms: List[JargonTerm] = Field(min_items=1, max_items=20)
    summary: Optional[str] = Field(None, description="Brief summary of complexity level")

# Viewpoints Schema
class NewsSource(str, Enum):
    KATHIMERINI = "Καθημερινή"
    TA_NEA = "Τα Νέα"
    PROTO_THEMA = "Πρώτο Θέμα"
    EFSYN = "Εφημερίδα των Συντακτών"
    CNN_GR = "CNN Greece"
    OTHER = "Άλλο"

class Viewpoint(BaseModel):
    perspective: str = Field(description="Brief title of perspective", max_length=100)
    argument: str = Field(description="Detailed explanation in Greek", min_length=50)
    source: NewsSource = Field(description="News source")
    source_url: Optional[str] = Field(None, description="Direct article URL if available")
    key_difference: str = Field(description="Main difference from original article")

class ViewpointsAnalysis(GreekContent):
    viewpoints: List[Viewpoint] = Field(min_items=2, max_items=6)
    consensus_points: List[str] = Field(description="Points all sources agree on")
    
# Fact Check Schema  
class Verdict(str, Enum):
    TRUE = "Αληθές"
    MOSTLY_TRUE = "Κυρίως Αληθές"  
    MIXED = "Μικτό"
    MISLEADING = "Παραπλανητικό"
    FALSE = "Ψευδές"
    UNVERIFIABLE = "Μη Επαληθεύσιμο"

class FactSource(BaseModel):
    description: str = Field(description="Source description in Greek")
    url: str = Field(description="Direct URL to source")
    reliability: str = Field(description="High/Medium/Low reliability indicator")

class FactClaim(BaseModel):
    claim: str = Field(description="Exact claim from article")
    verdict: Verdict
    explanation: str = Field(description="Detailed fact-check explanation", min_length=100)
    evidence: List[str] = Field(description="Key evidence points")
    sources: List[FactSource] = Field(min_items=1, max_items=5)

class FactCheckAnalysis(GreekContent):
    claims: List[FactClaim] = Field(min_items=1, max_items=10)
    overall_credibility: str = Field(description="Overall article credibility assessment")
    red_flags: List[str] = Field(description="Warning signs or issues found")
    missing_context: Optional[str] = Field(None, description="Important missing information")

# Bias Analysis Schema
class PoliticalPosition(str, Enum):
    FAR_LEFT = "Άκρα Αριστερά"
    LEFT = "Αριστερά"
    CENTER_LEFT = "Κεντροαριστερά"
    CENTER = "Κέντρο"
    CENTER_RIGHT = "Κεντροδεξιά"
    RIGHT = "Δεξιά"
    FAR_RIGHT = "Άκρα Δεξιά"

class BiasIndicator(BaseModel):
    indicator: str = Field(description="Specific bias indicator")
    example: str = Field(description="Example from article")
    impact: str = Field(description="How it affects objectivity")

class BiasAnalysis(GreekContent):
    political_leaning: PoliticalPosition
    economic_position: str = Field(description="Economic ideology position")
    bias_indicators: List[BiasIndicator] = Field(min_items=1, max_items=10)
    missing_perspectives: List[str] = Field(description="Viewpoints not represented")
    objectivity_score: int = Field(ge=1, le=10, description="1-10 objectivity rating")
    reasoning: str = Field(description="Detailed reasoning for assessment", min_length=200)

# Timeline Schema
class TimelineEvent(BaseModel):
    date: str = Field(description="Date in format: YYYY-MM-DD or 'περίπου YYYY-MM'")
    title: str = Field(description="Brief event title", max_length=100)
    description: str = Field(description="Detailed description in Greek")
    importance: str = Field(description="Κρίσιμο/Σημαντικό/Δευτερεύον")
    source: str = Field(description="Information source")
    verified: bool = Field(description="Whether event is verified")

class TimelineAnalysis(GreekContent):
    story_title: str = Field(description="Overall story title")
    events: List[TimelineEvent] = Field(min_items=3, max_items=20)
    duration: str = Field(description="Total timeline span")
    key_turning_points: List[str] = Field(description="Critical moments")
    future_implications: Optional[str] = Field(None, description="Potential future developments")

# Expert Opinions Schema
class ExpertCredentials(BaseModel):
    name: str = Field(description="Expert's full name")
    title: str = Field(description="Professional title in Greek")
    affiliation: str = Field(description="Organization or institution")
    expertise_area: str = Field(description="Area of expertise")

class ExpertOpinion(BaseModel):
    expert: ExpertCredentials
    stance: str = Field(description="Υπέρ/Κατά/Ουδέτερος/Μικτός")
    main_argument: str = Field(description="Core argument in Greek", min_length=100)
    key_quote: Optional[str] = Field(None, description="Notable quote if available")
    source_url: Optional[str] = Field(None, description="X post or article URL")
    date: Optional[str] = Field(None, description="Date of opinion")

class ExpertAnalysis(GreekContent):
    topic_summary: str = Field(description="Brief topic overview", max_length=200)
    experts: List[ExpertOpinion] = Field(min_items=2, max_items=10)
    consensus_level: str = Field(description="Πλήρης/Μερική/Ελάχιστη/Καμία")
    key_debates: List[str] = Field(description="Main points of disagreement")
    emerging_perspectives: Optional[List[str]] = Field(None, description="New viewpoints")

# X Pulse Schema (Complex)
class Sentiment(str, Enum):
    POSITIVE = "Θετικό"
    NEGATIVE = "Αρνητικό"
    MIXED = "Μικτό"
    NEUTRAL = "Ουδέτερο"

class XPost(BaseModel):
    content: str = Field(description="Post content (abbreviated if needed)", max_length=500)
    author_description: str = Field(description="Anonymous author type description")
    engagement_level: str = Field(description="High/Medium/Low engagement")
    timestamp_relative: Optional[str] = Field(None, description="e.g., '2 ώρες πριν'")

class DiscussionTheme(BaseModel):
    theme_title: str = Field(description="Theme title in Greek", max_length=100)
    theme_summary: str = Field(description="Detailed theme explanation", min_length=100)
    sentiment: Sentiment
    representative_posts: List[XPost] = Field(min_items=2, max_items=5)
    prevalence: str = Field(description="Κυρίαρχο/Συχνό/Μέτριο/Σπάνιο")

class XPulseAnalysis(GreekContent):
    overall_discourse_summary: str = Field(description="Executive summary", max_length=500)
    total_posts_analyzed: int = Field(ge=0, description="Approximate posts analyzed")
    discussion_themes: List[DiscussionTheme] = Field(min_items=2, max_items=8)
    trending_hashtags: Optional[List[str]] = Field(None, max_items=10)
    overall_sentiment: Sentiment
    key_influencers: Optional[List[str]] = Field(None, description="Key voices (anonymized)")
    data_caveats: str = Field(description="Important limitations or caveats")
