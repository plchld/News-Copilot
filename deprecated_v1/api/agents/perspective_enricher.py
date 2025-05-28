"""Perspective Enricher Agent - Extracts detailed perspectives from found articles"""

import json
from typing import Dict, Any, List
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel


class PerspectiveEnricher(AnalysisAgent):
    """Lightweight agent to extract detailed perspectives from articles"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'PerspectiveEnricher':
        """Factory method to create a configured PerspectiveEnricher"""
        config = AgentConfig(
            name="PerspectiveEnricher",
            description="Extracts detailed perspectives from articles",
            default_model=ModelType.GROK_3_MINI,  # Fast and cost-effective
            complexity=ComplexityLevel.LOW,
            supports_streaming=False,
            max_retries=2,
            timeout_seconds=30
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_enricher_prompt,
            schema_builder=lambda: {
                "type": "object",
                "properties": {
                    "key_argument": {"type": "string", "description": "Main argument in Greek"},
                    "supporting_points": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "2-3 supporting points in Greek"
                    },
                    "stance": {"type": "string", "description": "Overall stance in Greek"},
                    "relevance": {"type": "string", "description": "Why this perspective matters"}
                },
                "required": ["key_argument", "supporting_points", "stance"]
            }
        )
    
    @staticmethod
    def _build_enricher_prompt(context: Dict[str, Any]) -> str:
        """Build prompt for perspective enrichment"""
        original_topic = context.get('original_topic', '')
        article_title = context.get('article_title', '')
        
        return f"""Αναλύσε αυτό το άρθρο σε σχέση με το θέμα: "{original_topic}"

Εξήγησε:
1. Ποια είναι η βασική άποψη/επιχείρημα του άρθρου για αυτό το θέμα
2. Ποια στοιχεία υποστηρίζουν αυτή την άποψη (2-3 σημεία)
3. Ποια είναι η γενική στάση (θετική/αρνητική/ουδέτερη/μικτή)
4. Γιατί αυτή η οπτική είναι σημαντική για τον αναγνώστη

Τίτλος άρθρου: {article_title}

Απάντησε μόνο σε JSON format στα ελληνικά."""

    def _build_search_params(self, context: Dict[str, Any]) -> None:
        """No search needed for this agent"""
        return None


async def enrich_viewpoints(grok_client, viewpoints_data: List[Dict], original_topic: str) -> List[Dict]:
    """Enrich minimal viewpoints with detailed perspectives"""
    enricher = PerspectiveEnricher.create(grok_client)
    enriched_viewpoints = []
    
    for viewpoint in viewpoints_data:
        try:
            # Prepare context for enrichment
            context = {
                'original_topic': original_topic,
                'article_title': viewpoint.get('perspective', ''),
                'article_text': viewpoint.get('argument', ''),  # If available
                'session_id': f"enrich_{id(viewpoint)}"
            }
            
            # Get detailed perspective
            result = await enricher.execute(context)
            
            if result.success and result.data:
                # Merge enriched data with original viewpoint
                enriched_viewpoint = {
                    **viewpoint,  # Keep original data
                    'detailed_argument': result.data.get('key_argument', viewpoint.get('argument', '')),
                    'supporting_points': result.data.get('supporting_points', []),
                    'stance': result.data.get('stance', ''),
                    'relevance': result.data.get('relevance', '')
                }
                enriched_viewpoints.append(enriched_viewpoint)
            else:
                # Keep original if enrichment fails
                enriched_viewpoints.append(viewpoint)
                
        except Exception as e:
            print(f"[PerspectiveEnricher] Error enriching viewpoint: {str(e)}")
            # Keep original on error
            enriched_viewpoints.append(viewpoint)
    
    return enriched_viewpoints