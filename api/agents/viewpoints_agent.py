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
            prompt_builder=lambda ctx: GROK_ALTERNATIVE_VIEWPOINTS_PROMPT,
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
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for finding alternative viewpoints"""
        return {
            "mode": "on",
            "sources": [
                {"type": "news"},
                {"type": "web"}
            ],
            "return_citations": True,
            "max_search_results": 20
        }
    
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