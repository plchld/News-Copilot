"""Jargon Explanation Agent - Identifies and explains technical terms"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import JargonAnalysis # Added
from ..prompt_utils import get_task_instruction # Modified import


class JargonAgent(AnalysisAgent):
    """Jargon identification with structured outputs""" # Description updated
    
    @classmethod
    def create(cls, grok_client: Any) -> 'JargonAgent':
        """Factory method to create a configured JargonAgent"""
        config = AgentConfig(
            name="JargonAgent",
            description="Identifies technical terms with structured output", # Description updated
            default_model=ModelType.GROK_3_MINI,
            complexity=ComplexityLevel.SIMPLE,
            supports_streaming=True, # As per guide example
            max_retries=3,
            timeout_seconds=60
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_jargon_prompt,
            response_model=JargonAnalysis, # Added
            schema_builder=None # Explicitly set to None as response_model is used
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
        """Build prompt using centralized utilities""" # Docstring updated
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '')
        
        # Use centralized prompt
        base_prompt = get_task_instruction('jargon', article_content, article_url)
        
        # Add structured output guidance
        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Identify technical terms, organizations, and concepts that need explanation.
Focus on terms that a general Greek audience might not understand.
Provide clear, concise explanations in simple Greek."""
        
        return enhanced_prompt

    # _call_grok method is removed as the base class will handle it via _call_grok_structured or _call_grok_legacy