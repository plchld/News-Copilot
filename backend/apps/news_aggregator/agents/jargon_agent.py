"""
Jargon Agent - Explains technical terms in articles
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_jargon_response_schema
from ..claude_client import get_claude_client

logger = logging.getLogger(__name__)


class JargonAgent(AnalysisAgent):
    """Agent for identifying and explaining technical jargon"""
    
    def __init__(self):
        config = AgentConfig(
            name="jargon",
            description="Identifies and explains technical terms and jargon",
            default_model=ModelType.CLAUDE_HAIKU_3_5,
            complexity=ComplexityLevel.SIMPLE,
            timeout_seconds=60
        )
        schema = get_jargon_response_schema()
        super().__init__(config, schema)
        self.claude_client = get_claude_client()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for jargon analysis"""
        return """Είσαι ειδικός στην ανάλυση και επεξήγηση τεχνικών όρων και ορολογίας.

Ο στόχος σου είναι να:
1. Εντοπίσεις τεχνικούς όρους, ακρωνύμια και εξειδικευμένη ορολογία
2. Παρέχεις σαφείς, κατανοητές εξηγήσεις στα Ελληνικά
3. Δώσεις το πλαίσιο χρήσης κάθε όρου μέσα στο άρθρο

Οδηγίες:
- Εστίασε σε όρους που μπορεί να μην είναι κατανοητοί στο ευρύ κοινό
- Οι εξηγήσεις πρέπει να είναι σύντομες αλλά περιεκτικές
- Χρησιμοποίησε απλή γλώσσα στις εξηγήσεις
- Αν ένας όρος είναι ακρωνύμιο, εξήγησε τι σημαίνει"""
    
    def get_user_prompt(self, article_content: str) -> str:
        """Get the user prompt for analyzing the article"""
        return f"""Ανάλυσε το παρακάτω άρθρο και εντόπισε τους τεχνικούς όρους που χρειάζονται εξήγηση:

{article_content[:3000]}...

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        """Process the article to identify and explain jargon"""
        try:
            # Create the analysis request using Claude (no websearch needed for jargon)
            response = await self.claude_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                use_websearch=False,  # No websearch needed for jargon explanation
                temperature=0.3  # Lower temperature for more consistent results
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
            logger.error(f"Jargon agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )