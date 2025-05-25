"""Alternative Viewpoints Agent - Finds different perspectives on the same story"""

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
            default_model=ModelType.GROK_3,  # Using grok-3 as specified
            complexity=ComplexityLevel.MEDIUM,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=90
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_viewpoints_prompt,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "viewpoints": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        )
    
    @staticmethod
    def _build_viewpoints_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for finding alternative viewpoints"""
        # The full article text is passed via the user message in base_agent
        return """Find other credible news articles covering the SAME story.
Summarize in 4-8 bullet points how their coverage differs or adds to the original story.
Mention new facts, different perspectives, missing details, or conflicting statements.
ALL output must be in GREEK. Include source citations."""
    
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
                {"type": "web"},
                {"type": "x"}
            ],
            excluded_websites_map=create_exclusion_map_with_article_domain(article_domain),
            max_results=20
        )
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API for viewpoints analysis"""
        try:
            # Use the prompt from prompts.py
            system_prompt = GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + f"\n\nArticle:\n{context['article_text']}"
            
            response = await self.grok_client.create_completion(
                messages=[{"role": "user", "content": "Find alternative viewpoints for this article"}],
                system=system_prompt,
                response_format={"type": "json_object", "schema": schema},
                search_parameters=search_params,
                model=model.value
            )
            
            result = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {
                'data': result,
                'tokens_used': tokens_used
            }
            
        except Exception as e:
            self.logger.error(f"Grok API error in ViewpointsAgent: {str(e)}")
            raise


# Import the prompt from prompts.py
GROK_ALTERNATIVE_VIEWPOINTS_PROMPT = """Using Live Search, find other credible news articles that cover the SAME story as the original article provided below.
Summarize in 4-8 bullet points how their coverage differs or adds to the original story.
Mention new facts, different perspectives, missing details, or conflicting statements.
CRITICAL LANGUAGE REQUIREMENTS:
- Conduct searches primarily in GREEK to find Greek news sources
- The response MUST be exclusively in GREEK
- For each bullet point, please cite the source at the end of the point

X/TWITTER LINKS: If you reference X posts or X users, include @usernames in the text and full links where available.

IMPORTANT: The response must be objective and approach the story without bias.
"""