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
            prompt_builder=lambda ctx: GROK_BIAS_ANALYSIS_PROMPT,
            schema_builder=lambda: BIAS_ANALYSIS_SCHEMA
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for bias analysis"""
        # Build search params for bias analysis
        return {
            "mode": "on",
            "sources": [
                {"type": "news"},
                {"type": "web"},
                {"type": "x"}
            ],
            "return_citations": True,
            "max_search_results": 20
        }


GROK_BIAS_ANALYSIS_PROMPT = """Analyze the news article below for political bias, emotional tone, and presentation.

Using Live Search, compare the presentation with other sources covering the same topic.

Greek Political Spectrum Analysis:
Analyze the article based on the following two-dimensional Greek political spectrum:
1.  Economic Axis:
    *   Αριστερά (Κρατικός παρεμβατισμός, κοινωνικοποίηση μέσων παραγωγής, αναδιανομή πλούτου)
    *   Κεντροαριστερά (Μικτή οικονομία με ισχυρό κοινωνικό κράτος, ρύθμιση αγορών)
    *   Κέντρο (Ισορροπία μεταξύ ελεύθερης αγοράς και κοινωνικής προστασίας, δημοσιονομική υπευθυνότητα)
    *   Κεντροδεξιά (Ελεύθερη αγορά με στοχευμένες παρεμβάσεις, μείωση φορολογίας, προσέλκυση επενδύσεων)
    *   Δεξιά (Ελαχιστοποίηση κρατικής παρέμβασης, ιδιωτικοποιήσεις, πλήρης απελευθέρωση αγορών)
2.  Social Axis:
    *   Προοδευτική (Δικαιώματα ΛΟΑΤΚΙ+, διαχωρισμός κράτους-εκκλησίας, πολυπολιτισμικότητα, ατομικές ελευθερίες)
    *   Φιλελεύθερη (Έμφαση στα ατομικά δικαιώματα, ανεκτικότητα, μεταρρυθμίσεις)
    *   Συντηρητική (Έμφαση στην παράδοση, εθνική ταυτότητα, οικογενειακές αξίες, επιφυλακτικότητα σε ραγδαίες αλλαγές)

CRITICAL: Conduct searches in GREEK when possible for Greek sources. ALL responses must be in GREEK with objectivity.
"""

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