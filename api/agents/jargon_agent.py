"""Jargon Explanation Agent - Identifies and explains technical terms"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


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
            prompt_builder=lambda ctx: GROK_CONTEXT_JARGON_PROMPT_SCHEMA,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "terms": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "term": {"type": "string"},
                                "explanation": {"type": "string"}
                            },
                            "required": ["term", "explanation"]
                        }
                    }
                },
                "required": ["terms"]
            }
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for jargon lookup"""
        # Build search params for jargon
        return {
            "mode": "auto",
            "sources": [
                {"type": "web"},
                {"type": "news"}
            ],
            "return_citations": True,
            "max_search_results": 10
        }
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API for jargon analysis"""
        # Let the base class handle the API call
        return await super()._call_grok(prompt, schema, model, search_params, context)


# Import the prompt from prompts.py
GROK_CONTEXT_JARGON_PROMPT_SCHEMA = """Read the news article below.
Identify ONLY the NON-obvious technical terms, organizations, or historical references that an average reader might not be familiar with.
For each term, provide an explanation of 1-2 sentences IN GREEK.

Return the results as a JSON object containing a "terms" array with objects that have:
- "term": the term as it appears in the article
- "explanation": the explanation in Greek

IMPORTANT: Use Live Search with GREEK search terms when possible. ALL explanations must be written in GREEK. Only use English search terms when the specific term requires it (e.g., English technical terms, international organizations).
"""