"""Fact-Checking Agent - Verifies claims and statistics"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import FactCheckAnalysis, Verdict # Added
from ..prompt_utils import get_task_instruction # Added


class FactCheckAgent(AnalysisAgent):
    """Agent for fact-checking claims and verifying information using structured output""" # Updated description
    
    @classmethod
    def create(cls, grok_client: Any) -> 'FactCheckAgent':
        """Factory method to create a configured FactCheckAgent"""
        config = AgentConfig(
            name="FactCheckAgent",
            description="Verifies claims, statistics, and facts with structured output", # Updated description
            default_model=ModelType.GROK_3, 
            complexity=ComplexityLevel.MEDIUM, # As per original
            supports_streaming=True, # As per original
            max_retries=3,
            timeout_seconds=120
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_fact_check_prompt,
            response_model=FactCheckAnalysis, # Added
            schema_builder=None # Explicitly set to None
        )
    
    @staticmethod
    def _build_fact_check_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for fact-checking with structured output guidance."""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '')

        base_prompt = get_task_instruction('fact_check', article_content, article_url)

        # Guidance for FactCheckAnalysis schema:
        # claims: List[FactClaim] (min_items=1, max_items=10)
        #   FactClaim: claim, verdict (Verdict enum), explanation, evidence (List[str]), sources (List[FactSource])
        #     FactSource: description, url, reliability
        # overall_credibility: str
        # red_flags: List[str]
        # missing_context: Optional[str]
        
        # Dynamically create the list of valid Verdict string values for the prompt
        valid_verdicts = ", ".join([f"'{v.value}'" for v in Verdict])

        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Structure your response according to the 'FactCheckAnalysis' schema.
Analyze the provided article to identify key claims and verify them using external search if necessary.

For each claim identified (aim for 1-10 claims):
- claim: State the exact claim from the article.
- verdict: Assign a verdict from the following allowed values: {valid_verdicts}.
- explanation: Provide a detailed explanation for your verdict (min 100 characters).
- evidence: List key pieces of evidence that support your verdict.
- sources: Provide a list of 1-5 sources used for verification. Each source must include:
    - description: A brief description of the source in Greek.
    - url: The direct URL to the source.
    - reliability: Indicate source reliability (e.g., High/Medium/Low).

After analyzing individual claims, provide:
- overall_credibility: An overall assessment of the article's credibility in Greek.
- red_flags: A list of any warning signs or issues found (e.g., biased language, unsupported claims).
- missing_context: Optionally, describe any important missing information or context.

CRITICAL REQUIREMENTS:
- All text, including explanations, descriptions, and assessments, MUST be in GREEK.
- Focus on the most significant claims in the article.
- Ensure explanations are thorough and directly support the verdict.
"""
        return enhanced_prompt
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for fact-checking"""
        from ..search_params_builder import get_search_params_for_fact_check
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_fact_check(mode="on", article_domain=article_domain)