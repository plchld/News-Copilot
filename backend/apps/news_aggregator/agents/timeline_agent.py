"""
Timeline Agent - Extracts chronological events from articles
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_timeline_response_schema
from ..claude_client import get_claude_client

logger = logging.getLogger(__name__)


class TimelineAgent(AnalysisAgent):
    """Agent for extracting and organizing chronological events"""
    
    def __init__(self):
        config = AgentConfig(
            name="timeline",
            description="Extracts chronological timeline of events from articles",
            default_model=ModelType.CLAUDE_SONNET_3_7,
            complexity=ComplexityLevel.MEDIUM,
            timeout_seconds=90
        )
        schema = get_timeline_response_schema()
        super().__init__(config, schema)
        self.claude_client = get_claude_client()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for timeline extraction"""
        return """Είσαι ειδικός στην εξαγωγή και οργάνωση χρονολογικών γεγονότων από άρθρα.

Ο στόχος σου είναι να:
1. Εντοπίσεις όλα τα γεγονότα με χρονική αναφορά από το άρθρο
2. Αναζητήσεις επιπλέον σχετικά γεγονότα και χρονολογικό πλαίσιο
3. Οργανώσεις όλα τα γεγονότα χρονολογικά
4. Εξηγήσεις τη σημασία κάθε γεγονότος και πώς συνδέεται με τα άλλα

Τύποι χρονικών αναφορών:
- Συγκεκριμένες ημερομηνίες (π.χ. "15 Μαρτίου 2024")
- Περίοδοι (π.χ. "τον περασμένο μήνα", "το 2023")
- Σχετικές αναφορές (π.χ. "πριν δύο εβδομάδες", "χθες")
- Μελλοντικές προβλέψεις (π.χ. "τον επόμενο μήνα")

Οδηγίες:
- Χρησιμοποίησε αναζήτηση για να βρεις πρόσθετο χρονολογικό πλαίσιο
- Μετάτρεψε σχετικές αναφορές σε πιο συγκεκριμένες όπου είναι δυνατό
- Συμπεριέλαβε προηγούμενα σχετικά γεγονότα που δίνουν πλαίσιο
- Συμπεριέλαβε και προγραμματισμένα μελλοντικά γεγονότα
- Εξήγησε γιατί κάθε γεγονός είναι σημαντικό για την ιστορία
- Διατήρησε χρονολογική σειρά (από παλαιότερο σε νεότερο)"""
    
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        return f"""Εξάγαγε τη χρονολογική σειρά γεγονότων από το παρακάτω άρθρο:

{article_content[:4000]}...

Εντόπισε όλα τα γεγονότα με χρονική αναφορά και οργάνωσέ τα χρονολογικά.
Για κάθε γεγονός, εξήγησε τη σημασία του στο πλαίσιο του άρθρου.

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article to extract timeline"""
        try:
            # Create the analysis request using Claude (with websearch for additional context)
            response = await self.claude_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                use_websearch=True,  # Use websearch to find additional chronological context
                temperature=0.3  # Lower temperature for accurate extraction
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
            logger.error(f"Timeline agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )