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
            prompt_builder=lambda ctx: "Create a timeline for the events in this article. Use Live Search to find historical context. All output in Greek.",
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
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        # Build search params for timeline with date range
        from datetime import datetime, timedelta
        today = datetime.now().date()
        from_date = (today - timedelta(days=30)).isoformat()
        
        return {
            "mode": "on",
            "sources": [
                {"type": "news"},
                {"type": "web"}
            ],
            "from_date": from_date,
            "to_date": today.isoformat(),
            "return_citations": True,
            "max_search_results": 15
        }