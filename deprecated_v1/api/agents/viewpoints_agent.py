"""Alternative Viewpoints Agent - Finds different perspectives on the same story"""

import json
from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import get_viewpoints_response_schema


class ViewpointsAgent(AnalysisAgent):
    """Agent for finding alternative viewpoints and perspectives"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ViewpointsAgent':
        """Factory method to create a configured ViewpointsAgent"""
        config = AgentConfig(
            name="ViewpointsAgent",
            description="Finds alternative viewpoints and perspectives",
            default_model=ModelType.GROK_3_FAST,  # Use fast for faster response
            complexity=ComplexityLevel.MEDIUM,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=120  # Increased timeout for live search
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_viewpoints_prompt,
            schema_builder=get_viewpoints_response_schema
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for finding alternative viewpoints"""
        try:
            from api.utils.search_params_builder import build_search_params, create_exclusion_map_with_article_domain
        except ImportError:
            # Fallback to basic search params
            return {
                "mode": "on",
                "sources": [{"type": "news"}, {"type": "web"}],
                "max_results": 15
            }
        
        from urllib.parse import urlparse
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        # Log search parameter building
        logger.info(f"[ViewpointsAgent] Building search params for article: {article_url}")
        logger.info(f"[ViewpointsAgent] Excluding domain: {article_domain}")
        
        # Alternative viewpoints should always exclude the source
        search_params = build_search_params(
            mode="on",
            sources=[
                {"type": "news"},
                {"type": "web"}
            ],  # Removed X source for faster search
            excluded_websites_map=create_exclusion_map_with_article_domain(article_domain),
            max_results=15  # Reduced for faster search
        )
        
        logger.info(f"[ViewpointsAgent] Search params built: {json.dumps(search_params, ensure_ascii=False, indent=2)}")
        
        return search_params
    
    @staticmethod
    def _build_viewpoints_prompt(context: Dict[str, Any]) -> str:
        """Build the complete prompt for viewpoints analysis"""
        import logging
        logger = logging.getLogger(__name__)
        
        article_text = context.get('article_text', '')
        logger.info(
            f"[ViewpointsAgent] Building prompt | "
            f"Article length: {len(article_text)} chars | "
            f"First 200 chars: {article_text[:200]}..."
        )
        
        # Note: Article text is passed separately in base_agent
        return GROK_ALTERNATIVE_VIEWPOINTS_PROMPT


# Enhanced prompt for comprehensive viewpoint analysis
GROK_ALTERNATIVE_VIEWPOINTS_PROMPT = """Είσαι αναλυτής ειδήσεων του News-Copilot. Βρες και σύνθεσε εναλλακτικές οπτικές για το κύριο θέμα του άρθρου χρησιμοποιώντας live search.

ΣΤΟΧΟΣ: Βοήθησε τους αναγνώστες να κατανοήσουν το πλήρες φάσμα απόψεων γύρω από το θέμα.

ΜΟΡΦΗ ΑΠΑΝΤΗΣΗΣ - ΧΡΗΣΙΜΟΠΟΙΗΣΕ MARKDOWN:

## Ανάλυση Θέματος
[Σύντομη εξήγηση του κύριου θέματος σε 1-2 προτάσεις]

## Εναλλακτικές Οπτικές

### Υποστηρικτική Άποψη
[Εξήγηση της υποστηρικτικής οπτικής - ΤΙ υποστηρίζουν και ΓΙΑΤΙ]

### Κριτική Προσέγγιση
[Εξήγηση της κριτικής οπτικής - ΤΙ επικρίνουν και ΓΙΑΤΙ]

### Ουδέτερη/Εναλλακτική Λύση
[Εξήγηση εναλλακτικών προσεγγίσεων ή λύσεων]

## Κύριες Πηγές
- [Πηγή 1]: [Σύντομη περίληψη της οπτικής]
- [Πηγή 2]: [Σύντομη περίληψη της οπτικής]
- [Πηγή 3]: [Σύντομη περίληψη της οπτικής]

ΟΔΗΓΙΕΣ:
1. ΕΝΤΟΠΙΣΕ το κεντρικό θέμα του άρθρου
2. ΑΝΑΖΗΤΗΣΕ άλλη κάλυψη του θέματος (όχι το ίδιο άρθρο)
3. ΣΥΝΘΕΣΕ διαφορετικές οπτικές σε οργανωμένη επισκόπηση
4. Χρησιμοποίησε **bold** για έμφαση σε κλειδιά
5. Εξήγησε ΓΙΑΤΙ διαφωνούν τα μέρη, όχι μόνο ΟΤΙ διαφωνούν
6. Στόχευσε σε 3-4 ξεκάθαρες οπτικές για σαφήνεια

ΣΗΜΑΝΤΙΚΟ: Απάντησε ΜΟΝΟ με καθαρό markdown στα Ελληνικά."""