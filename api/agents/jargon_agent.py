"""Jargon Explanation Agent - Identifies and explains technical terms"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from ..prompt_utils import get_jargon_task_instruction, get_jargon_response_schema


class JargonAgent(AnalysisAgent):
    """Agent for identifying and explaining technical terms in Greek"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'JargonAgent':
        """Factory method to create a configured JargonAgent"""
        config = AgentConfig(
            name="JargonAgent",
            description="Identifies technical terms and provides Greek explanations",
            default_model=ModelType.GROK_3_MINI,  # Only top-level agent using mini
            complexity=ComplexityLevel.SIMPLE,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=60
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_jargon_prompt,
            schema_builder=get_jargon_response_schema
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for jargon lookup"""
        from ..search_params_builder import get_search_params_for_jargon
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_jargon(mode="auto", article_domain=article_domain)
    
    @staticmethod
    def _build_jargon_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for jargon extraction"""
        # For grok-3-mini, use a concise prompt without redundant instructions
        # The full article text is passed via the user message in base_agent
        return """Identify technical terms, organizations, and historical references that need explanation.
Provide brief explanations (1-2 sentences) in GREEK for each term."""
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API for jargon analysis"""
        # Let the base class handle the API call
        return await super()._call_grok(prompt, schema, model, search_params, context)