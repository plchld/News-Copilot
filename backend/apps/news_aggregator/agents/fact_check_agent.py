"""
Fact Check Agent - Verifies claims and statements in articles
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_fact_check_response_schema
from ..grok_client import get_grok_client

logger = logging.getLogger(__name__)


class FactCheckAgent(AnalysisAgent):
    """Agent for fact-checking claims and verifying statements"""
    
    def __init__(self):
        config = AgentConfig(
            name="fact_check",
            description="Verifies claims and checks facts in articles",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.HIGH,
            timeout_seconds=120
        )
        schema = get_fact_check_response_schema()
        super().__init__(config, schema)
        self.grok_client = get_grok_client()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for fact-checking analysis"""
        return """Είσαι ειδικός στον έλεγχο γεγονότων και την επαλήθευση ισχυρισμών.

Ο στόχος σου είναι να:
1. Εντοπίσεις τους κύριους ισχυρισμούς και δηλώσεις στο άρθρο
2. Αξιολογήσεις την ποιότητα των τεκμηρίων για κάθε ισχυρισμό
3. Παρέχεις πλαίσιο και εξήγηση για την αξιολόγησή σου
4. Αναζητήσεις επιπλέον πηγές όταν χρειάζεται

Κριτήρια αξιολόγησης:
- "ισχυρά τεκμηριωμένο": Πολλαπλές αξιόπιστες πηγές, σαφή στοιχεία
- "μερικώς τεκμηριωμένο": Κάποια στοιχεία αλλά όχι πλήρης τεκμηρίωση
- "αμφιλεγόμενο": Αντικρουόμενες πληροφορίες από αξιόπιστες πηγές
- "ελλιπώς τεκμηριωμένο": Ελάχιστα ή αδύναμα στοιχεία
- "χωρίς επαρκή στοιχεία": Δεν υπάρχουν διαθέσιμα στοιχεία
- "εκτός πλαισίου": Ο ισχυρισμός είναι εκτός του πεδίου επαλήθευσης

Οδηγίες:
- Εστίασε σε ουσιαστικούς, επαληθεύσιμους ισχυρισμούς
- Αγνόησε απόψεις και υποκειμενικές κρίσεις
- Χρησιμοποίησε live search για να βρεις επιπλέον πληροφορίες
- Να είσαι αντικειμενικός και ισορροπημένος"""
    
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        return f"""Ανάλυσε το παρακάτω άρθρο και έλεγξε τους κύριους ισχυρισμούς:

{article_content[:4000]}...

Εντόπισε τους επαληθεύσιμους ισχυρισμούς και αξιολόγησε την τεκμηρίωσή τους.
Χρησιμοποίησε live search για να βρεις επιπλέον πληροφορίες όπου χρειάζεται.

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article to fact-check claims"""
        try:
            # Create the analysis request with search enabled
            response = await self.grok_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                temperature=0.3,  # Lower temperature for factual accuracy
                search_enabled=True  # Enable live search for fact-checking
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
            logger.error(f"Fact check agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )