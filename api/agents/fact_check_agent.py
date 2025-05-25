"""Fact-Checking Agent - Verifies claims and statistics"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class FactCheckAgent(AnalysisAgent):
    """Agent for fact-checking claims and verifying information"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'FactCheckAgent':
        """Factory method to create a configured FactCheckAgent"""
        config = AgentConfig(
            name="FactCheckAgent",
            description="Verifies claims, statistics, and facts",
            default_model=ModelType.GROK_3,  # Using grok-3 as specified
            complexity=ComplexityLevel.MEDIUM,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=120
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_fact_check_prompt,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "overall_credibility": {
                        "type": "string",
                        "enum": ["υψηλή", "μέτρια", "χαμηλή"]
                    },
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string"},
                                "verified": {"type": "boolean"},
                                "explanation": {"type": "string"},
                                "sources": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["statement", "verified", "explanation", "sources"]
                        }
                    },
                    "red_flags": {"type": "array", "items": {"type": "string"}},
                    "missing_context": {"type": "string"}
                },
                "required": ["overall_credibility", "claims"]
            }
        )
    
    @staticmethod
    def _build_fact_check_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for fact-checking"""
        # The full article text is passed via the user message in base_agent
        return """Verify the main claims, statistics, dates, and events in the article.
Focus on the 3-5 most important claims.
ALL explanations and warnings must be in GREEK."""
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for fact-checking"""
        from ..search_params_builder import get_search_params_for_fact_check
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_fact_check(mode="on", article_domain=article_domain)