"""Timeline Agent - Creates chronological event timelines"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import TimelineAnalysis # Added
from ..prompt_utils import get_task_instruction # Added


class TimelineAgent(AnalysisAgent):
    """Agent for creating event timelines using structured output""" # Updated description
    
    @classmethod
    def create(cls, grok_client: Any) -> 'TimelineAgent':
        config = AgentConfig(
            name="TimelineAgent",
            description="Creates chronological timelines of events with structured output", # Updated description
            default_model=ModelType.GROK_3, # As per original
            complexity=ComplexityLevel.MEDIUM, # As per original
            # As per guide, supports_streaming defaults to True in AgentConfig, 
            # max_retries to 3, timeout_seconds to 120.
            # Original had timeout_seconds=90. Keeping 90.
            supports_streaming=True, # Assuming, not specified in original but typical
            max_retries=3,
            timeout_seconds=90 # Kept from original
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_timeline_prompt,
            response_model=TimelineAnalysis, # Added
            schema_builder=None # Explicitly set to None
        )
    
    @staticmethod
    def _build_timeline_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for timeline creation with structured output guidance."""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '') # For get_task_instruction

        # Use the centralized get_task_instruction
        base_prompt = get_task_instruction('timeline', article_content, article_url)

        # Guidance for TimelineAnalysis schema:
        # story_title: str
        # events: List[TimelineEvent] (min_items=3, max_items=20)
        #   TimelineEvent: date, title, description, importance, source, verified
        # duration: str
        # key_turning_points: List[str]
        # future_implications: Optional[str]

        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Structure your response according to the 'TimelineAnalysis' schema.
Create a chronological timeline of the key events described in or relevant to the article.

Provide the following overall timeline information:
- story_title: A concise overall title for the story or events.
- duration: The total time span covered by the timeline (e.g., "3 months", "2 years").
- key_turning_points: A list of critical moments or events that significantly changed the course of the story.
- future_implications: (Optional) Potential future developments or consequences related to the timeline.

For each event in the timeline (aim for 3-20 events):
- date: The date of the event. Use "YYYY-MM-DD" format if exact, or "περίπου YYYY-MM" (around YYYY-MM) if approximate.
- title: A brief, descriptive title for the event (max 100 characters).
- description: A detailed description of the event in Greek.
- importance: Assess the event's importance as "Κρίσιμο" (Critical), "Σημαντικό" (Important), or "Δευτερεύον" (Secondary).
- source: The source of information for this event (e.g., specific news report, official document).
- verified: Indicate if the event is verified (true/false).

CRITICAL REQUIREMENTS:
- All titles, descriptions, and analyses MUST be in GREEK.
- Ensure the events are in chronological order.
- Focus on factual events directly related to or providing essential context for the article's main subject.
"""
        return enhanced_prompt
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for timeline analysis"""
        from ..search_params_builder import get_search_params_for_timeline
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_timeline(mode="on", article_domain=article_domain)