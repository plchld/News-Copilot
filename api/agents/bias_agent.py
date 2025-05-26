"""Bias Analysis Agent - Analyzes political bias and framing"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import BiasAnalysis, PoliticalPosition # Added BiasIndicator implicitly used via BiasAnalysis
from ..prompt_utils import get_task_instruction # Added


class BiasAnalysisAgent(AnalysisAgent):
    """Political bias analysis with structured outputs""" # Updated description
    
    @classmethod
    def create(cls, grok_client: Any) -> 'BiasAnalysisAgent':
        """Factory method to create a configured BiasAnalysisAgent"""
        config = AgentConfig(
            name="BiasAnalysisAgent",
            description="Analyzes political bias with structured output", # Updated description
            default_model=ModelType.GROK_3, # As per guide
            complexity=ComplexityLevel.COMPLEX, # As per guide
            supports_streaming=False, # As per guide example for BiasAnalysisAgent
            max_retries=2, # As per guide example
            timeout_seconds=120 # As per guide example
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_bias_prompt,
            response_model=BiasAnalysis, # Added
            schema_builder=None # Explicitly set to None
        )
    
    @staticmethod
    def _build_bias_prompt(context: Dict[str, Any]) -> str:
        """Build comprehensive bias analysis prompt with structured output guidance."""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '')

        base_prompt = get_task_instruction('bias', article_content, article_url)
        
        # Dynamically create the list of valid PoliticalPosition string values for the prompt
        valid_positions = ", ".join([f"'{p.value}'" for p in PoliticalPosition])

        # Guidance for BiasAnalysis schema:
        # political_leaning: PoliticalPosition
        # economic_position: str
        # bias_indicators: List[BiasIndicator] (min_items=1, max_items=10)
        #   BiasIndicator: indicator, example, impact
        # missing_perspectives: List[str]
        # objectivity_score: int (ge=1, le=10)
        # reasoning: str (min_length=200)

        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Structure your response according to the 'BiasAnalysis' schema.
Analyze the provided article for political bias, economic positioning, specific bias indicators, missing perspectives, and overall objectivity.

Provide the following information:
- political_leaning: Determine the article's political leaning on the Greek political spectrum. Choose from: {valid_positions}.
- economic_position: Describe the economic ideology or position reflected in the article (e.g., neoliberal, social democratic, Keynesian, etc.).
- bias_indicators: Identify 1-10 specific bias indicators. For each indicator:
    - indicator: Name the type of bias (e.g., "Loaded Language", "Selective Omission", "Source Bias").
    - example: Provide a direct quote or specific example from the article.
    - impact: Explain how this indicator affects the article's objectivity.
- missing_perspectives: List viewpoints or perspectives that are notably absent from the article, which, if included, would provide a more balanced view.
- objectivity_score: Rate the article's objectivity on a scale of 1 to 10 (1 being highly biased, 10 being perfectly objective).
- reasoning: Provide a detailed reasoning (min 200 characters) for your overall assessment, explaining how you arrived at the political leaning, economic position, and objectivity score based on the identified indicators and missing perspectives.

CRITICAL REQUIREMENTS:
- All analysis, descriptions, and reasoning MUST be in GREEK.
- Ensure the reasoning is comprehensive and clearly links the evidence (bias indicators, missing perspectives) to the conclusions (leaning, score).
"""
        return enhanced_prompt
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for bias analysis - bias analysis doesn't need live search"""
        # Bias analysis should be based solely on article content, not external sources
        return None

# Removed BIAS_ANALYSIS_SCHEMA global variable