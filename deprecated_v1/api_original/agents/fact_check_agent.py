"""Fact-Checking Agent - Verifies claims and statistics"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import get_fact_check_response_schema


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
            timeout_seconds=300
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_fact_check_prompt,
            schema_builder=get_fact_check_response_schema
        )
    
    @staticmethod
    def _build_fact_check_prompt(context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for rigorous fact-checking"""
        return """Είσαι ο News-Copilot, ειδικός στον έλεγχο γεγονότων για Έλληνες αναγνώστες.

ΑΠΟΣΤΟΛΗ: Επαλήθευσε τους 3-5 πιο σημαντικούς ισχυρισμούς του άρθρου με αυστηρά κριτήρια.

ΜΟΡΦΗ ΑΠΑΝΤΗΣΗΣ - ΧΡΗΣΙΜΟΠΟΙΗΣΕ MARKDOWN:

## Έλεγχος Ισχυρισμών

### Ισχυρισμός 1: [Ακριβής διατύπωση του ισχυρισμού από το άρθρο]
**Αξιολόγηση**: [Μία από: ισχυρά τεκμηριωμένο / μερικώς τεκμηριωμένο / αμφιλεγόμενο / ελλιπώς τεκμηριωμένο / χωρίς επαρκή στοιχεία / εκτός πλαισίου]
**Εξήγηση**: [Λεπτομερής εξήγηση του ελέγχου - τουλάχιστον 100 χαρακτήρες]
**Πηγές**:
- [Πηγή 1]
- [Πηγή 2]

### Ισχυρισμός 2: [...]
[Συνέχισε με τον ίδιο τρόπο]

## Ποιότητα Πηγών
**Πρωτογενείς πηγές**: [αριθμός]
**Δευτερογενείς πηγές**: [αριθμός]  
**Ποικιλία πηγών**: [υψηλή / μέτρια / χαμηλή]

ΚΡΙΤΗΡΙΑ ΑΞΙΟΛΟΓΗΣΗΣ:
- **ισχυρά τεκμηριωμένο**: Επαληθεύεται από πολλές αξιόπιστες πηγές
- **μερικώς τεκμηριωμένο**: Γενικά σωστό με μικρές ανακρίβειες  
- **αμφιλεγόμενο**: Υπάρχουν αντικρουόμενες απόψεις
- **ελλιπώς τεκμηριωμένο**: Λίγα στοιχεία υποστήριξης
- **χωρίς επαρκή στοιχεία**: Δεν μπορεί να επαληθευτεί
- **εκτός πλαισίου**: Παραπλανητική παρουσίαση

ΣΗΜΑΝΤΙΚΟ: Απάντησε με καθαρό markdown χρησιμοποιώντας την παραπάνω δομή."""
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for fact-checking"""
        try:
            from api.utils.search_params_builder import get_search_params_for_fact_check
        except ImportError:
            # Provide comprehensive search params for fact-checking
            from urllib.parse import urlparse
            article_url = context.get('article_url', '')
            parsed_url = urlparse(article_url)
            article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
            
            excluded_sites = [article_domain] if article_domain else []
            
            return {
                "mode": "on",
                "sources": [
                    {"type": "news", "excluded_websites": excluded_sites},
                    {"type": "web", "excluded_websites": excluded_sites}
                ],
                "country": "GR",
                "language": "el",
                "include_english": True,  # Include English for international sources
                "max_results": 25,  # More results for thorough fact-checking
                "safe_search": True
            }
        
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_fact_check(mode="on", article_domain=article_domain)