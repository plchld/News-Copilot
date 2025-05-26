"""Expert Opinions Agent - Finds expert opinions on the topic"""

from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import ExpertAnalysis # ExpertCredentials, ExpertOpinion are part of ExpertAnalysis
from ..prompt_utils import get_task_instruction # Added


class ExpertOpinionsAgent(AnalysisAgent):
    """Agent for finding expert opinions using structured output""" # Updated description
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ExpertOpinionsAgent':
        config = AgentConfig(
            name="ExpertOpinionsAgent",
            description="Finds expert opinions and viewpoints with structured output", # Updated description
            default_model=ModelType.GROK_3, # As per original
            complexity=ComplexityLevel.MEDIUM, # As per original
            # Assuming default streaming, retries. Original timeout_seconds=90
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=90 # Kept from original
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_expert_prompt,
            response_model=ExpertAnalysis, # Added
            schema_builder=None # Explicitly set to None
        )
    
    @staticmethod
    def _build_expert_prompt(context: Dict[str, Any]) -> str:
        """Build optimized prompt for expert opinions with structured output guidance."""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '') # For get_task_instruction

        # Use the centralized get_task_instruction
        # Assuming 'expert_opinions' is a valid task type for get_task_instruction
        base_prompt = get_task_instruction('expert_opinions', article_content, article_url)

        # Guidance for ExpertAnalysis schema:
        # topic_summary: str (max_length=200)
        # experts: List[ExpertOpinion] (min_items=2, max_items=10)
        #   ExpertOpinion: expert (ExpertCredentials), stance, main_argument, key_quote, source_url, date
        #     ExpertCredentials: name, title, affiliation, expertise_area
        # consensus_level: str (e.g., "Πλήρης/Μερική/Ελάχιστη/Καμία")
        # key_debates: List[str]
        # emerging_perspectives: Optional[List[str]]

        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Structure your response according to the 'ExpertAnalysis' schema.
Identify and summarize opinions from relevant experts on the main topic of the article.

Provide the following overall analysis:
- topic_summary: A brief overview of the topic being discussed by experts (max 200 characters).
- consensus_level: Describe the level of consensus among experts (e.g., "Πλήρης", "Μερική", "Ελάχιστη", "Καμία").
- key_debates: List the main points of disagreement or debate among the experts.
- emerging_perspectives: (Optional) List any new or developing perspectives on the topic.

For each expert identified (aim for 2-10 experts):
- expert: Provide the expert's credentials:
    - name: Full name of the expert.
    - title: Professional title in Greek.
    - affiliation: Organization or institution.
    - expertise_area: Specific area of expertise relevant to the topic.
- stance: Indicate the expert's stance on the topic (e.g., "Υπέρ", "Κατά", "Ουδέτερος", "Μικτός").
- main_argument: Summarize the expert's core argument in Greek (min 100 characters).
- key_quote: (Optional) Include a notable quote from the expert if available.
- source_url: (Optional) Provide a URL to the X post, article, or source of the opinion.
- date: (Optional) The date the opinion was expressed.

CRITICAL REQUIREMENTS:
- All summaries, arguments, and expert details MUST be in GREEK.
- Focus on experts whose opinions are directly relevant to the article's main subject.
- Use external search to find credible expert opinions if not sufficiently present in the article.
"""
        return enhanced_prompt
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build search parameters for expert opinions"""
        from ..search_params_builder import get_search_params_for_expert_opinions
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it
        article_url = context.get('article_url', '')
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else None
        
        return get_search_params_for_expert_opinions(mode="on", article_domain=article_domain)