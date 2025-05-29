"""Bias Analysis Agent - Analyzes political bias and framing"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import get_bias_analysis_response_schema


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
            schema_builder=get_bias_analysis_response_schema
        )
    
    @staticmethod
    def _build_bias_prompt(context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for Greek political bias analysis"""
        return """Είσαι ο News-Copilot, ειδικός αναλυτής πολιτικής προκατάληψης για το ελληνικό πολιτικό φάσμα.

ΑΠΟΣΤΟΛΗ: Ανάλυσε την πολιτική τοποθέτηση και προκαταλήψεις του άρθρου με βάση το ελληνικό πολιτικό πλαίσιο.

ΕΛΛΗΝΙΚΟ ΠΟΛΙΤΙΚΟ ΦΑΣΜΑ:

Οικονομικός Άξονας:
- Αριστερά: Κρατικός παρεμβατισμός, κοινωνικό κράτος, αναδιανομή
- Κεντροαριστερά: Μικτή οικονομία, κοινωνική προστασία
- Κέντρο: Ισορροπία αγοράς-κράτους
- Κεντροδεξιά: Ελεύθερη αγορά με κανόνες
- Δεξιά: Ελεύθερη αγορά, ιδιωτικοποιήσεις, χαμηλή φορολογία

Κοινωνικός Άξονας:
- Προοδευτική: Δικαιώματα ΛΟΑΤΚΙ+, πολυπολιτισμικότητα, εκκοσμίκευση
- Φιλελεύθερη: Ατομικές ελευθερίες, ανοχή στη διαφορετικότητα
- Μετριοπαθής: Σταδιακές αλλαγές, παραδοσιακές αξίες με ανοχή
- Συντηρητική: Παράδοση, θρησκεία, οικογένεια, εθνική ταυτότητα

ΣΤΟΙΧΕΙΑ ΠΡΟΣ ΑΝΑΛΥΣΗ:
1. Επιλογή λέξεων και φράσεων (φορτισμένοι όροι)
2. Ποιες φωνές/πηγές προβάλλονται vs αποσιωπούνται
3. Πλαισίωση γεγονότων (framing)
4. Συναισθηματικός τόνος (θετικός/αρνητικός/ουδέτερος)
5. Υπονοούμενα και υποθέσεις

ΠΑΡΑΔΕΙΓΜΑΤΑ ΕΝΔΕΙΚΤΙΚΩΝ ΟΡΩΝ:
- Αριστερά: "νεοφιλελευθερισμός", "κοινωνική δικαιοσύνη", "εργατική τάξη"
- Δεξιά: "ανάπτυξη", "επενδύσεις", "εθνικό συμφέρον"
- Προοδευτική: "ανθρώπινα δικαιώματα", "ισότητα", "διαφορετικότητα"
- Συντηρητική: "παράδοση", "οικογενειακές αξίες", "εθνική κυριαρχία"

ΤΕΛΙΚΗ ΑΞΙΟΛΟΓΗΣΗ:
- economic_axis_placement: Τοποθέτηση στον οικονομικό άξονα
- social_axis_placement: Τοποθέτηση στον κοινωνικό άξονα
- overall_confidence: Υψηλή/Μέτρια/Χαμηλή βεβαιότητα για την αξιολόγηση
- Λεπτομερής αιτιολόγηση με συγκεκριμένα παραδείγματα από το κείμενο
- Εντοπισμός φορτισμένων όρων και τεχνικών πλαισίωσης
- Ποιες απόψεις/φωνές λείπουν από το άρθρο"""
    
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