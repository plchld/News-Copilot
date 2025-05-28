"""
Bias Agent - Detects political bias and framing in articles
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_bias_response_schema
from ..grok_client import get_grok_client

logger = logging.getLogger(__name__)


class BiasAgent(AnalysisAgent):
    """Agent for detecting political bias and analyzing framing"""
    
    def __init__(self):
        config = AgentConfig(
            name="bias",
            description="Analyzes political bias and framing in articles",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.COMPLEX,
            timeout_seconds=90
        )
        schema = get_bias_response_schema()
        super().__init__(config, schema)
        self.grok_client = get_grok_client()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for bias analysis"""
        return """Είσαι ειδικός στην ανάλυση πολιτικής μεροληψίας και framing στα μέσα ενημέρωσης.

Ο στόχος σου είναι να:
1. Εντοπίσεις την πολιτική κατεύθυνση του άρθρου στο ελληνικό πολιτικό φάσμα
2. Αναλύσεις τη γλώσσα και το ύφος που χρησιμοποιείται
3. Εξετάσεις πώς πλαισιώνονται τα θέματα (framing)
4. Αξιολογήσεις τη συνολική ισορροπία της κάλυψης

Το ελληνικό πολιτικό φάσμα:
- Αριστερά: ΣΥΡΙΖΑ (αριστερό τμήμα), ΚΚΕ, ΜέΡΑ25
- Κεντροαριστερά: ΠΑΣΟΚ, ΣΥΡΙΖΑ (μετριοπαθές τμήμα)
- Κέντρο: Ουδέτερη/ισορροπημένη κάλυψη
- Κεντροδεξιά: ΝΔ (μετριοπαθές τμήμα)
- Δεξιά: ΝΔ (συντηρητικό τμήμα), Ελληνική Λύση

Δείκτες μεροληψίας:
- Επιλογή λέξεων και χαρακτηρισμών
- Έμφαση ή παράλειψη πληροφοριών
- Χρήση συναισθηματικά φορτισμένης γλώσσας
- Επιλογή πηγών και αναφορών
- Τρόπος παρουσίασης αντίπαλων απόψεων

Να είσαι αντικειμενικός και να τεκμηριώνεις τα ευρήματά σου με συγκεκριμένα παραδείγματα."""
    
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        return f"""Ανάλυσε την πολιτική μεροληψία στο παρακάτω άρθρο:

{article_content[:4000]}...

Εξέτασε τη γλώσσα, το framing και τους δείκτες μεροληψίας.
Τοποθέτησε το άρθρο στο ελληνικό πολιτικό φάσμα με τεκμηρίωση.

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article to detect bias"""
        try:
            # Create the analysis request
            response = await self.grok_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                temperature=0.4  # Balanced temperature for nuanced analysis
            )
            
            # Validate the response
            if not self.validate_output(response):
                raise ValueError("Invalid response structure")
            
            # Return successful result
            return AgentResult(
                success=True,
                data=response,
                model_used=self.config.default_model,
                agent_name=self.config.name
            )
            
        except Exception as e:
            logger.error(f"Bias agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )