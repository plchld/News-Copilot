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
            prompt_builder=lambda ctx: "Find expert opinions on this topic using Live Search. Focus on X/Twitter and news sources. All output in Greek.",
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
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        # Build search params for expert opinions
        return {
            "mode": "on",
            "sources": [
                {"type": "x"},
                {"type": "news"},
                {"type": "web"}
            ],
            "return_citations": True,
            "max_search_results": 20
        }