"""
Viewpoints Agent - Finds alternative perspectives on topics
"""
from typing import Dict, Any
import logging

from .base import AnalysisAgent, AgentConfig, AgentResult, ModelType, ComplexityLevel
from .schemas import get_viewpoints_response_schema
from ..claude_client import get_claude_client

logger = logging.getLogger(__name__)


class ViewpointsAgent(AnalysisAgent):
    """Agent for finding alternative viewpoints and perspectives"""
    
    def __init__(self):
        config = AgentConfig(
            name="viewpoints",
            description="Discovers alternative perspectives and viewpoints on the topic",
            default_model=ModelType.CLAUDE_SONNET_4,
            complexity=ComplexityLevel.HIGH,
            timeout_seconds=120
        )
        schema = get_viewpoints_response_schema()
        super().__init__(config, schema)
        self.claude_client = get_claude_client()
    
    def get_system_prompt(self) -> str:
        return """Είσαι ειδικός στην ανάλυση διαφορετικών οπτικών γωνιών και απόψεων.

Ο στόχος σου είναι να:
1. Εντοπίσεις το κεντρικό θέμα του άρθρου
2. Αναζητήσεις και παρουσιάσεις εναλλακτικές οπτικές γωνίες
3. Συνθέσεις μια ολοκληρωμένη εικόνα των διαφορετικών απόψεων

Χρησιμοποίησε την αναζήτηση για να βρεις διαφορετικές προσεγγίσεις στο θέμα.
Αναζήτησε ενεργά για εναλλακτικές απόψεις και διαφορετικές οπτικές γωνίες."""
    
    def get_user_prompt(self, article_content: str) -> str:
        return f"""Ανάλυσε το παρακάτω άρθρο και βρες εναλλακτικές οπτικές γωνίες:

{article_content[:3000]}...

Απάντησε σε JSON με τη δομή που σου δόθηκε."""
    
    async def process(self, article_content: str, **kwargs) -> AgentResult:
        try:
            # Create the analysis request using Claude with websearch for alternative viewpoints
            response = await self.claude_client.create_structured_completion(
                system_prompt=self.get_system_prompt(),
                user_prompt=self.get_user_prompt(article_content),
                schema=self.schema,
                model=self.config.default_model.value,
                use_websearch=True,  # Essential for finding alternative perspectives
                temperature=0.7  # Higher temperature for diverse viewpoints
            )
            
            return AgentResult(
                success=True,
                data=response,
                model_used=self.config.default_model,
                agent_name=self.config.name
            )
            
        except Exception as e:
            logger.error(f"Viewpoints agent error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.config.name
            )