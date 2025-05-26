"""Alternative Viewpoints Agent - Finds different perspectives on the same story"""

import json
from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class ViewpointsAgent(AnalysisAgent):
    """Agent for finding alternative viewpoints and perspectives"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ViewpointsAgent':
        """Factory method to create a configured ViewpointsAgent"""
        config = AgentConfig(
            name="ViewpointsAgent",
            description="Finds alternative viewpoints and perspectives",
            default_model=ModelType.GROK_3_MINI,  # Use mini for faster response
            complexity=ComplexityLevel.MEDIUM,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=120  # Increased timeout for live search
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=lambda context: "",  # Not used since we have _build_custom_prompt
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "viewpoints": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "perspective": {"type": "string", "description": "The main perspective or angle"},
                                "argument": {"type": "string", "description": "The detailed argument or explanation"},
                                "source": {"type": "string", "description": "The source of this viewpoint"}
                            },
                            "required": ["perspective", "argument"]
                        }
                    }
                },
                "required": ["viewpoints"]
            }
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
            ],  # Removed X source for faster search
            excluded_websites_map=create_exclusion_map_with_article_domain(article_domain),
            max_results=15  # Reduced for faster search
        )
    
    def _build_custom_prompt(self, context: Dict[str, Any]) -> str:
        """Build the complete prompt including the article for viewpoints analysis"""
        return GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + f"\n\nArticle:\n{context['article_text']}"


# Updated prompt to match the new schema
GROK_ALTERNATIVE_VIEWPOINTS_PROMPT = """Using Live Search, find other credible news articles that cover the SAME story as the original article provided below.

For each different perspective or coverage angle you find, create a viewpoint object with:
- perspective: A brief title describing the angle or perspective (e.g., "Κυβερνητική Θέση", "Αντιπολιτευτική Κριτική", "Διεθνής Άποψη")
- argument: A detailed explanation of how this coverage differs, what new facts it adds, or what different perspective it offers
- source: The name of the news source (e.g., "Καθημερινή", "Τα Νέα", "BBC Greek")

CRITICAL REQUIREMENTS:
- Find 3-6 different viewpoints/perspectives
- Conduct searches primarily in GREEK to find Greek news sources  
- The response MUST be exclusively in GREEK
- Focus on how each source's coverage DIFFERS from or ADDS TO the original article
- Include new facts, different perspectives, missing details, or conflicting statements
- Be objective and approach the story without bias

Return the results as a JSON object with a "viewpoints" array containing the viewpoint objects.
"""