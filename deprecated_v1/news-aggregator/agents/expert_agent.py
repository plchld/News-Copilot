"""Expert Opinions Agent - Finds expert opinions on the topic"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class ExpertOpinionsAgent(AnalysisAgent):
    """Agent for finding expert opinions"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ExpertOpinionsAgent':
        config = AgentConfig(
            name="ExpertOpinionsAgent",
            description="Finds expert opinions and viewpoints",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.MEDIUM,
            timeout_seconds=90
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_expert_prompt,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "topic_summary": {"type": "string"},
                    "experts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "credentials": {"type": "string"},
                                "opinion": {"type": "string"},
                                "quote": {"type": "string"},
                                "source": {"type": "string"},
                                "source_url": {"type": "string"},
                                "stance": {"type": "string", "enum": ["υποστηρικτική", "αντίθετη", "ουδέτερη"]}
                            }
                        }
                    },
                    "consensus": {"type": "string"},
                    "key_debates": {"type": "string"}
                }
            }
        )
    
    @staticmethod
    def _build_expert_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for expert opinions"""
        # Use the expert opinions task instruction from utils.prompt_utils
        from utils.prompt_utils import get_expert_opinions_task_instruction
        article_text = context.get('article_text', '')
        return get_expert_opinions_task_instruction(article_text)
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for expert opinions"""
        from utils.search_params_builder import get_search_params_for_expert_opinions
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_expert_opinions(mode="on", article_domain=article_domain)