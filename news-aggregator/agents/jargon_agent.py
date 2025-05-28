"""Jargon Explanation Agent - Identifies and explains technical terms"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import get_jargon_response_schema


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
            prompt_builder=cls._build_jargon_prompt,
            schema_builder=get_jargon_response_schema
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for jargon lookup"""
        try:
            from utils.search_params_builder import get_search_params_for_jargon
        except ImportError:
            # Fallback to basic search params
            return None
        
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_jargon(mode="auto", article_domain=article_domain)
    
    @staticmethod
    def _build_jargon_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for jargon extraction"""
        return """Είσαι ο News-Copilot. Εντόπισε ΜΟΝΟ τους όρους που χρειάζονται εξήγηση για τον μέσο Έλληνα αναγνώστη.

ΜΟΡΦΗ ΑΠΑΝΤΗΣΗΣ - ΧΡΗΣΙΜΟΠΟΙΗΣΕ MARKDOWN:

## Επεξήγηση Όρων

**Όρος 1**: Σύντομη, κατανοητή εξήγηση (1-2 προτάσεις). Πρακτική σημασία για τον αναγνώστη αν υπάρχει.

**Όρος 2**: Σύντομη, κατανοητή εξήγηση (1-2 προτάσεις). Πρακτική σημασία για τον αναγνώστη αν υπάρχει.

[Συνέχισε με τον ίδιο τρόπο για κάθε όρο]

ΚΡΙΤΗΡΙΑ ΕΠΙΛΟΓΗΣ ΟΡΩΝ:
1. Τεχνικοί όροι που ΔΕΝ είναι ευρέως γνωστοί (π.χ. "blockchain" ναι, "internet" όχι)
2. Διεθνείς οργανισμοί με σημαντικό ρόλο (π.χ. "FATF", "EBA")  
3. Νομικοί/οικονομικοί όροι που επηρεάζουν πολίτες (π.χ. "ENFIA", "spread")
4. Ιστορικές αναφορές που χρειάζονται πλαίσιο (π.χ. "Συμφωνία των Πρεσπών")
5. Ακρωνύμια που ΔΕΝ είναι καθημερινά (π.χ. "QE" ναι, "ΕΕ" όχι)

ΜΗΝ ΣΥΜΠΕΡΙΛΑΒΕΙΣ:
- Κοινούς όρους (π.χ. κυβέρνηση, υπουργός, οικονομία)
- Γνωστά ακρωνύμια (π.χ. ΕΕ, ΗΠΑ, ΟΗΕ)
- Απλές λέξεις που υπάρχουν στο λεξικό

ΣΗΜΑΝΤΙΚΟ: Απάντησε με καθαρό markdown χρησιμοποιώντας την παραπάνω δομή."""
    
    async def _call_grok(self, prompt: str, schema: Dict, model: ModelType,
                        search_params: Optional[Dict], context: Dict) -> Dict:
        """Call Grok API for jargon analysis"""
        # Let the base class handle the API call
        return await super()._call_grok(prompt, schema, model, search_params, context)