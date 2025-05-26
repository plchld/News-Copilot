"""Alternative Viewpoints Agent - Finds different perspectives on the same story"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import ViewpointsAnalysis # Added
from ..prompt_utils import get_task_instruction # Added


class ViewpointsAgent(AnalysisAgent):
    """Agent for finding alternative viewpoints and perspectives using structured output""" # Updated description
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ViewpointsAgent':
        """Factory method to create a configured ViewpointsAgent"""
        config = AgentConfig(
            name="ViewpointsAgent",
            description="Finds alternative viewpoints with structured output", # Updated description
            default_model=ModelType.GROK_3_MINI, 
            complexity=ComplexityLevel.MEDIUM,
            supports_streaming=True, # As per JargonAgent example in guide
            max_retries=3,
            timeout_seconds=120
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_viewpoints_prompt, # Changed to static method
            response_model=ViewpointsAnalysis, # Added
            schema_builder=None # Explicitly set to None
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for finding alternative viewpoints"""
        from ..search_params_builder import build_search_params, create_exclusion_map_with_article_domain
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        # Alternative viewpoints should always exclude the source
        return build_search_params(
            mode="on",
            sources=[
                {"type": "news"},
                {"type": "web"}
            ],
            excluded_websites_map=create_exclusion_map_with_article_domain(article_domain),
            max_results=15
        )

    @staticmethod
    def _build_viewpoints_prompt(context: Dict[str, Any]) -> str:
        """Builds the prompt for the ViewpointsAgent using structured output guidance."""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '') # Needed for get_task_instruction

        # Use centralized prompt via get_task_instruction
        # Assuming 'viewpoints' is a valid task type for get_task_instruction
        base_prompt = get_task_instruction('viewpoints', article_content, article_url)

        # Add structured output guidance based on ViewpointsAnalysis schema
        # The ViewpointsAnalysis schema includes:
        # viewpoints: List[Viewpoint] (min_items=2, max_items=6)
        #   Viewpoint: perspective, argument, source (NewsSource enum), source_url, key_difference
        # consensus_points: List[str]
        
        enhanced_prompt = f"""{base_prompt}

Using Live Search, find other credible news articles that cover the SAME story as the original article.
Your goal is to identify different viewpoints or perspectives on the events.

IMPORTANT: Structure your response according to the 'ViewpointsAnalysis' schema.
For each viewpoint, provide:
- perspective: A brief title for the perspective (e.g., "Government Stance", "Opposition Critique", "International Reaction").
- argument: A detailed explanation of this viewpoint, focusing on how it differs or what new information it adds.
- source: The news source name (e.g., "{', '.join(item.value for item in ViewpointsAnalysis.__fields__['viewpoints'].type_.__fields__['source'].type_)}").
- source_url: The direct URL to the article presenting this viewpoint, if available.
- key_difference: Concisely state the main difference of this viewpoint compared to the original article's narrative.

Also, identify 'consensus_points': a list of key facts or statements that most sources, including the original, seem to agree upon.

CRITICAL REQUIREMENTS:
- Identify 2-6 distinct viewpoints.
- All explanations and titles must be in GREEK.
- Focus on how coverage DIFFERS or ADDS to the original article.
- Be objective and cover various angles.
"""
        return enhanced_prompt

# Removed GROK_ALTERNATIVE_VIEWPOINTS_PROMPT global variable
# Removed _build_custom_prompt method, replaced by _build_viewpoints_prompt