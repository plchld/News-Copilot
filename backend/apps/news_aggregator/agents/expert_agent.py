"""
Expert Agent - Synthesizes expert perspectives on article topics
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_expert_response_schema
from ..grok_client import get_grok_client

logger = logging.getLogger(__name__)


class ExpertAgent(AnalysisAgent):
    """Agent for synthesizing expert perspectives on topics"""
    
    def __init__(self):
        config = AgentConfig(
            name="expert",
            description="Synthesizes expert perspectives and opinions on article topics",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.COMPLEX,
            timeout_seconds=120
        )
        schema = get_expert_response_schema()
        super().__init__(config, schema)
        self.grok_client = get_grok_client()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for expert analysis"""
        return """Είσαι ειδικός στη σύνθεση απόψεων εμπειρογνωμόνων από διάφορους τομείς.

Ο στόχος σου είναι να:
1. Προσδιορίσεις τον κύριο τομέα εξειδίκευσης που απαιτείται
2. Συνθέσεις απόψεις από διαφορετικές ειδικότητες
3. Εντοπίσεις σημεία συναίνεσης μεταξύ ειδικών
4. Αναδείξεις σημεία διαφωνίας ή συζήτησης

Τομείς εξειδίκευσης που μπορεί να χρειαστούν:
- Οικονομία και χρηματοοικονομικά
- Πολιτική επιστήμη και διεθνείς σχέσεις
- Νομικά θέματα και συνταγματικό δίκαιο
- Υγεία και ιατρική
- Τεχνολογία και καινοτομία
- Περιβάλλον και κλιματική αλλαγή
- Κοινωνιολογία και κοινωνικές επιστήμες
- Εκπαίδευση και παιδαγωγική

Οδηγίες:
- Χρησιμοποίησε live search για να βρεις απόψεις ειδικών
- Σύνθεσε διαφορετικές προοπτικές με ισορροπημένο τρόπο
- Απόδωσε κάθε άποψη στον κατάλληλο τομέα εξειδίκευσης
- Ανάδειξε τόσο τις συμφωνίες όσο και τις διαφωνίες"""
    
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        return f"""Ανάλυσε το παρακάτω άρθρο και σύνθεσε απόψεις εμπειρογνωμόνων:

{article_content[:4000]}...

Προσδιόρισε ποιοι τομείς εξειδίκευσης σχετίζονται με το θέμα.
Χρησιμοποίησε live search για να βρεις απόψεις ειδικών.
Σύνθεσε τις διαφορετικές προοπτικές και ανάδειξε συμφωνίες/διαφωνίες.

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article to synthesize expert perspectives"""
        try:
            # Create the analysis request with search enabled
            response = await self.grok_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                temperature=0.5,  # Moderate temperature for creative synthesis
                search_enabled=True  # Enable live search for expert opinions
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
            logger.error(f"Expert agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )