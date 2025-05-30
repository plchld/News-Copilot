"""Configuration for orchestration"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class StoryPriority(Enum):
    """Priority levels for stories"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration process"""
    
    # Provider configuration
    discovery_provider: str = "grok"  # Good for search
    greek_perspective_provider: str = "grok"  # Good for Greek content
    international_provider: str = "grok"  # Good for search
    opposing_view_provider: str = "grok"  # Good for search
    fact_check_provider: str = "grok"  # Good for search
    synthesis_provider: str = "anthropic"  # Best for synthesis
    jargon_provider: str = "grok"  # Fast and accurate
    timeline_provider: str = "grok"  # Good for historical search
    social_provider: str = "grok"  # Only Grok has X access
    
    # Discovery settings
    categories_to_scan: List[str] = None  # None means all
    max_stories_per_category: int = 5
    discovery_time_range: str = "today"
    
    # Analysis settings
    max_stories_to_analyze: int = 10
    min_greek_relevance: float = 0.3
    parallel_perspective_agents: int = 4
    
    # Synthesis settings
    narrative_max_words: int = 400
    include_timeline: bool = True
    include_jargon: bool = True
    include_social_pulse: bool = True
    
    # Performance settings
    agent_timeout_seconds: int = 30
    max_retries: int = 3
    cache_results: bool = True
    
    # Output settings
    output_format: str = "json"  # json, markdown, html
    include_confidence_scores: bool = True
    include_source_attribution: bool = True
    
    def __post_init__(self):
        """Set defaults if not provided"""
        if self.categories_to_scan is None:
            self.categories_to_scan = [
                "greek_politics",
                "global_politics", 
                "economy_business",
                "science_tech",
                "society_culture"
            ]
    
    def get_provider_for_agent(self, agent_type: str) -> str:
        """Get the configured provider for a specific agent type"""
        provider_map = {
            "discovery": self.discovery_provider,
            "greek_perspective": self.greek_perspective_provider,
            "international_perspective": self.international_provider,
            "opposing_view": self.opposing_view_provider,
            "fact_verification": self.fact_check_provider,
            "narrative_synthesis": self.synthesis_provider,
            "jargon_context": self.jargon_provider,
            "timeline": self.timeline_provider,
            "social_pulse": self.social_provider
        }
        return provider_map.get(agent_type, "grok")


@dataclass
class StorySelectionCriteria:
    """Criteria for selecting which stories to analyze"""
    
    min_sources: int = 3  # Minimum sources covering the story
    min_greek_relevance: float = 0.3
    required_categories: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    priority_keywords: Optional[List[str]] = None
    
    def meets_criteria(self, story: Dict) -> bool:
        """Check if a story meets selection criteria"""
        # Check minimum sources
        if story.get("initial_sources_found", 0) < self.min_sources:
            return False
        
        # Check Greek relevance
        if story.get("greek_relevance", 0) < self.min_greek_relevance:
            return False
        
        # Check excluded keywords
        if self.excluded_keywords:
            headline_lower = story.get("headline", "").lower()
            for keyword in self.excluded_keywords:
                if keyword.lower() in headline_lower:
                    return False
        
        return True
    
    def calculate_priority(self, story: Dict) -> float:
        """Calculate priority score for a story"""
        score = 0.0
        
        # Base score from Greek relevance
        score += story.get("greek_relevance", 0) * 0.4
        
        # Source count factor
        sources = story.get("initial_sources_found", 0)
        score += min(sources / 20, 0.3)  # Cap at 0.3
        
        # Category match factor
        score += story.get("category_match", 0.5) * 0.3
        
        # Priority keywords boost
        if self.priority_keywords:
            headline_lower = story.get("headline", "").lower()
            for keyword in self.priority_keywords:
                if keyword.lower() in headline_lower:
                    score += 0.1
                    break
        
        return min(score, 1.0)  # Cap at 1.0