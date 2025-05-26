"""Bias Analysis Agent - Analyzes political bias and framing"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class BiasAnalysisAgent(AnalysisAgent):
    """Agent for analyzing political bias and language framing"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'BiasAnalysisAgent':
        """Factory method to create a configured BiasAnalysisAgent"""
        config = AgentConfig(
            name="BiasAnalysisAgent",
            description="Analyzes political bias, tone, and framing",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.HIGH,
            supports_streaming=True,
            timeout_seconds=120
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_bias_prompt,
            schema_builder=lambda: BIAS_ANALYSIS_SCHEMA
        )
    
    @staticmethod
    def _build_bias_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for bias analysis"""
        # The full article text is passed via the user message in base_agent
        return """Analyze political bias, emotional tone, and presentation in the article.
Compare with other sources on the same topic.

Place on Greek political spectrum:
Economic: Αριστερά/Κεντροαριστερά/Κέντρο/Κεντροδεξιά/Δεξιά
Social: Προοδευτική/Φιλελεύθερη/Μετριοπαθής/Συντηρητική

ALL analysis and justifications must be in GREEK."""
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for bias analysis - bias analysis doesn't need live search"""
        # Bias analysis should be based solely on article content, not external sources
        # We don't need live search to determine if something is biased
        return None

BIAS_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "political_spectrum_analysis_greek": {
            "type": "object",
            "properties": {
                "economic_axis_placement": {
                    "type": "string",
                    "enum": ["Αριστερά", "Κεντροαριστερά", "Κέντρο", "Κεντροδεξιά", "Δεξιά", "Ουδέτερο", "Άγνωστο/Δεν είναι σαφές"]
                },
                "economic_axis_justification": {"type": "string"},
                "social_axis_placement": {
                    "type": "string",
                    "enum": ["Προοδευτική", "Φιλελεύθερη", "Μετριοπαθής", "Συντηρητική", "Άγνωστο/Δεν είναι σαφές"]
                },
                "social_axis_justification": {"type": "string"},
                "overall_confidence": {
                    "type": "string",
                    "enum": ["Υψηλή", "Μέτρια", "Χαμηλή"]
                }
            },
            "required": ["economic_axis_placement", "economic_axis_justification", 
                        "social_axis_placement", "social_axis_justification", "overall_confidence"]
        },
        "language_and_framing_analysis": {
            "type": "object",
            "properties": {
                "emotionally_charged_terms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["term", "explanation"]
                    }
                },
                "identified_framing_techniques": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "technique_name": {"type": "string"},
                            "example_from_article": {"type": "string"}
                        },
                        "required": ["technique_name", "example_from_article"]
                    }
                },
                "detected_tone": {
                    "type": "string",
                    "enum": ["θετικός", "αρνητικός", "ουδέτερος", "μικτός", "άγνωστος"]
                },
                "missing_perspectives_summary": {"type": "string"}
            },
            "required": ["emotionally_charged_terms", "identified_framing_techniques", 
                        "detected_tone", "missing_perspectives_summary"]
        },
        "comparison": {"type": "string"},
        "recommendations": {"type": "string"}
    },
    "required": ["political_spectrum_analysis_greek", "language_and_framing_analysis"]
}