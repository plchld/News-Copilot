"""Timeline Agent - Creates chronological event timelines"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class TimelineAgent(AnalysisAgent):
    """Agent for creating event timelines"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'TimelineAgent':
        config = AgentConfig(
            name="TimelineAgent",
            description="Creates chronological timelines of events",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.MEDIUM,
            timeout_seconds=90
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_timeline_prompt,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "story_title": {"type": "string"},
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "importance": {"type": "string", "enum": ["υψηλή", "μέτρια", "χαμηλή"]},
                                "source": {"type": "string"}
                            }
                        }
                    },
                    "context": {"type": "string"},
                    "future_implications": {"type": "string"}
                }
            }
        )
    
    @staticmethod
    def _build_timeline_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for timeline creation"""
        # Use the timeline task instruction from utils.prompt_utils
        from utils.prompt_utils import get_timeline_task_instruction
        article_text = context.get('article_text', '')
        return get_timeline_task_instruction(article_text)
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for timeline analysis"""
        from utils.search_params_builder import get_search_params_for_timeline
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_timeline(mode="on", article_domain=article_domain)