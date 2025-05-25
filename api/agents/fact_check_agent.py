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
            prompt_builder=lambda ctx: GROK_FACT_CHECK_PROMPT,
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
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for fact-checking"""
        # Build search params for fact-checking
        return {
            "mode": "on",
            "sources": [
                {"type": "web"},
                {"type": "news"}
            ],
            "return_citations": True,
            "max_search_results": 25
        }


# Import the prompt from prompts.py
GROK_FACT_CHECK_PROMPT = """Analyze the news article below for fact-checking.

Using Live Search, verify the main claims, statistics, dates, and events mentioned in the article.

Return JSON with the structure:
{
  "overall_credibility": "υψηλή/μέτρια/χαμηλή",
  "claims": [
    {
      "statement": "The specific claim from the article",
      "verified": true/false,
      "explanation": "Verification explanation in Greek",
      "sources": ["source1", "source2"]
    }
  ],
  "red_flags": ["Warning 1", "Warning 2"],
  "missing_context": "Information that is missing or needs clarification"
}

Focus on the 3-5 most important claims. 

CRITICAL: Conduct searches in GREEK when possible. ALL responses must be in GREEK.
"""