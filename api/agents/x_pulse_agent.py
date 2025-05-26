"""X Pulse Agent - Analyzes X (Twitter) discourse with nested sub-agents"""

from typing import Dict, Any, List, Optional
from .base_agent import NestedAgent, AnalysisAgent, AgentConfig, ModelType, ComplexityLevel, AgentResult
from ..schemas import XPulseAnalysis, DiscussionTheme, XPost, Sentiment # Import main schemas
from pydantic import BaseModel, Field # For local sub-agent schemas
from datetime import datetime
import asyncio
# import json # Not explicitly used at top level after changes

# --- Pydantic Models for Sub-agent Outputs (Locally Defined for Simplicity) ---
class KeywordExtractionResult(BaseModel):
    main_topic: str = Field(description="Core subject of the article.")
    key_entities: List[str] = Field(description="List of important people, organizations, locations, or specific terms mentioned.")
    x_search_keywords: List[str] = Field(description="List of 3-5 keywords or short phrases for X search in Greek.")

class XSearchResultItem(BaseModel):
    content: str = Field(description="Content of the X post.")
    # theme: str = Field(description="Preliminary theme assigned to the post.") # Theme assignment might be complex for search agent
    # relevance: str = Field(description="Relevance of the post (e.g., high, medium, low).") # Relevance might be hard for LLM to judge without more context
    # Simplified XSearch output to focus on retrieving posts, further analysis by other agents
    author_description: Optional[str] = Field(None, description="Brief anonymous description of the post author.")
    engagement_level: Optional[str] = Field(None, description="Estimated engagement (e.g., High/Medium/Low).")
    timestamp_relative: Optional[str] = Field(None, description="e.g., '2 hours ago'")


class XSearchResults(BaseModel):
    posts: List[XSearchResultItem] = Field(description="List of relevant X posts found.")

class SubAgentTheme(BaseModel): # Intermediate theme representation
    theme_title: str = Field(description="Concise title for the discussion theme in Greek (2-5 words).")
    theme_summary: str = Field(description="1-2 sentence summary of the theme in Greek.")
    representative_examples: List[str] = Field(description="List of example post contents representing this theme.")
    sentiment_label: str = Field(description="Overall sentiment of this theme (e.g., Positive, Negative, Neutral, Mixed).") # To be mapped to Sentiment enum

class SubAgentThemeList(BaseModel):
    themes: List[SubAgentTheme]

# SentimentAnalyzerAgent might not be strictly needed if ThemeAnalyzerAgent provides a sentiment_label
# Or, it could refine the sentiment_label into the Sentiment enum and add justification.
# For now, let's assume ThemeAnalyzerAgent provides a sentiment_label and XPulseAgent maps it.

class KeywordExtractorAgent(AnalysisAgent):
    """Sub-agent for extracting keywords from article"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'KeywordExtractorAgent':
        config = AgentConfig(
            name="KeywordExtractorAgent",
            description="Extracts keywords for X search using structured output",
            default_model=ModelType.GROK_3_MINI,
            complexity=ComplexityLevel.SIMPLE,
            timeout_seconds=30
        )
        
        def build_prompt(context):
            # Using KeywordExtractionResult field descriptions in prompt
            return f"""Analyze the provided news article text.
Identify and extract the following, ensuring your output matches the requested structure:
1. Main Topic: {KeywordExtractionResult.__fields__['main_topic'].field_info.description}
2. Key Entities: {KeywordExtractionResult.__fields__['key_entities'].field_info.description}
3. Search Keywords: {KeywordExtractionResult.__fields__['x_search_keywords'].field_info.description}

Article Text:
{context['article_text'][:2000]}..."""
        
        return cls(
            config, 
            grok_client, 
            build_prompt, 
            response_model=KeywordExtractionResult, # Use Pydantic model
            schema_builder=None
        )


class XSearchAgent(AnalysisAgent):
    """Sub-agent for searching X posts and returning them in a structured way"""
    # This agent primarily uses the search tool. The LLM call might be minimal,
    # perhaps just to format or slightly filter if the search tool isn't perfect.
    # The prompt below assumes it's more about instructing the search and light formatting.
    # If the search tool itself can return structured XPost-like objects, LLM might not be needed here.
    # However, the original had a schema, implying an LLM call.
    
    @classmethod
    def create(cls, grok_client: Any) -> 'XSearchAgent':
        config = AgentConfig(
            name="XSearchAgent",
            description="Searches X posts based on keywords and returns structured results.",
            default_model=ModelType.GROK_3_MINI, 
            complexity=ComplexityLevel.MEDIUM, # Increased complexity due to search interpretation
            timeout_seconds=60
        )
        
        def build_prompt(context):
            keywords = context.get('keywords', [])
            keyword_str = ", ".join(keywords)
            # The prompt should guide the LLM to process search results from the tool
            # and structure them according to XSearchResults -> List[XSearchResultItem]
            return f"""Based on the X (Twitter) search results for keywords: "{keyword_str}",
Please format these search results into a list of posts.
For each post, extract or determine:
- content: The main text of the X post.
- author_description: A brief, anonymized description of the author (e.g., "Journalist", "Concerned Citizen", "Politician").
- engagement_level: An estimation of engagement (High, Medium, Low) based on likes, reposts, if available.
- timestamp_relative: A relative timestamp like "2 hours ago", if available.

Focus on Greek language posts. Filter out irrelevant or purely promotional content.
Present up to 20 relevant posts.
"""
        
        return cls(
            config, 
            grok_client, 
            build_prompt, 
            response_model=XSearchResults, # Use Pydantic model
            schema_builder=None
        )
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build X-specific search parameters"""
        keywords = context.get('keywords', [])
        # Ensure keywords is a list of strings
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            self.logger.warning(f"Keywords are not a list of strings: {keywords}. Skipping X search.")
            return None
        if not keywords:
            self.logger.warning("No keywords provided for X search. Skipping.")
            return None
            
        search_query = " OR ".join(keywords) + " lang:el" # Ensure lang:el for Greek posts
        
        return {
            "mode": "on", # Ensure search is active
            "sources": [{"type": "x"}], # Specify X as the source
            "return_citations": False, # Citations might not be directly useful for LLM processing here
            "max_search_results": 30 # Number of search results to consider
        }


class ThemeAnalyzerAgent(AnalysisAgent):
    """Sub-agent for identifying discussion themes from X posts"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ThemeAnalyzerAgent':
        config = AgentConfig(
            name="ThemeAnalyzerAgent",
            description="Identifies discussion themes from X posts using structured output",
            default_model=ModelType.GROK_3, 
            complexity=ComplexityLevel.HIGH,
            timeout_seconds=90
        )
        
        def build_prompt(context):
            posts_data = context.get('posts_data', []) # Expects XSearchResults model or its dict version
            
            if isinstance(posts_data, XSearchResults):
                posts_content = [p.content for p in posts_data.posts[:50]] # Use Pydantic model
            elif isinstance(posts_data, dict) and 'posts' in posts_data: # Handle dict if necessary
                posts_content = [p.get('content', '') for p in posts_data['posts'][:50]]
            else:
                posts_content = []

            if not posts_content:
                return "No posts provided for theme analysis. Please return an empty list of themes."

            posts_text = "\n".join([f"- {content}" for content in posts_content])
            
            return f"""Analyze these X posts and identify 3-5 dominant themes or distinct viewpoints.
For each theme, provide:
1. theme_title: {SubAgentTheme.__fields__['theme_title'].field_info.description}
2. theme_summary: {SubAgentTheme.__fields__['theme_summary'].field_info.description}
3. representative_examples: A list of 2-3 direct quotes from the posts that best represent this theme.
4. sentiment_label: {SubAgentTheme.__fields__['sentiment_label'].field_info.description} (e.g., Positive, Negative, Neutral, Mixed, Highly Critical).

Posts to analyze:
{posts_text}

All output must be in Greek. Structure your response as a list of themes.
"""
        
        return cls(
            config, 
            grok_client, 
            build_prompt, 
            response_model=SubAgentThemeList, # Use Pydantic model
            schema_builder=None
        )

# SentimentAnalyzerAgent is removed as its functionality can be integrated into ThemeAnalyzerAgent
# by asking for a 'sentiment_label', and then XPulseAgent can map this to the Sentiment enum.
# This simplifies the chain from 4 sub-agents to 3 for the LLM-based part.
# The original SentimentAnalyzerAgent was also very simple and could be merged.

class XPulseAgent(NestedAgent):
    """Main X Pulse agent that coordinates sub-agents"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'XPulseAgent':
        """Factory method to create a configured XPulseAgent with sub-agents"""
        config = AgentConfig(
            name="XPulseAgent",
            description="Analyzes X discourse using nested agents and structured output",
            default_model=ModelType.GROK_3, 
            complexity=ComplexityLevel.VERY_HIGH,
            supports_streaming=True, # Assuming, was True
            timeout_seconds=180 # As original
        )
        
        # Create sub-agents - SentimentAnalyzerAgent is removed
        sub_agents = [
            KeywordExtractorAgent.create(grok_client),
            XSearchAgent.create(grok_client),
            ThemeAnalyzerAgent.create(grok_client)
            # SentimentAnalyzerAgent.create(grok_client) # Removed
        ]
        
        return cls(config, grok_client, sub_agents)
    
    async def _execute_sub_agents(self, context: Dict[str, Any]) -> List[AgentResult]:
        """Custom orchestration for X Pulse sub-agents."""
        session_id = context.get('session_id', 'unknown')
        orchestration_start = datetime.now()
        results = []
        num_sub_agents = len(self.sub_agents)

        self.logger.info(
            f"[X_PULSE_ORCHESTRATION] {session_id} - Starting {num_sub_agents}-stage X Pulse analysis | "
            f"Sub-agents: {[agent.config.name for agent in self.sub_agents]}"
        )

        # Step 1: Extract keywords
        keyword_result: Optional[AgentResult] = None
        try:
            keyword_agent = self.sub_agents[0]
            self.logger.info(f"[X_PULSE_STEP1] {session_id} - Starting {keyword_agent.config.name}")
            keyword_result = await keyword_agent.execute(context)
            results.append(keyword_result)
            if not keyword_result.success or not keyword_result.data:
                self.logger.error(f"[X_PULSE_STEP1] FAILED: {keyword_result.error}")
                return results # Cannot proceed without keywords
            
            # Ensure data is the Pydantic model instance
            if not isinstance(keyword_result.data, KeywordExtractionResult):
                 keyword_result.data = KeywordExtractionResult(**keyword_result.data) # Parse if dict

            self.logger.info(f"[X_PULSE_STEP1] SUCCESS. Keywords: {keyword_result.data.x_search_keywords}")
        except Exception as e:
            self.logger.error(f"[X_PULSE_STEP1] Exception: {str(e)}")
            results.append(AgentResult(success=False, error=str(e), agent_name=self.sub_agents[0].config.name))
            return results

        # Step 2: Search X with extracted keywords
        x_search_result: Optional[AgentResult] = None
        try:
            search_agent = self.sub_agents[1]
            search_context = {**context, 'keywords': keyword_result.data.x_search_keywords}
            self.logger.info(f"[X_PULSE_STEP2] {session_id} - Starting {search_agent.config.name}")
            x_search_result = await search_agent.execute(search_context)
            results.append(x_search_result)
            if not x_search_result.success or not x_search_result.data:
                self.logger.error(f"[X_PULSE_STEP2] FAILED: {x_search_result.error}. Proceeding with empty posts.")
                x_search_result.data = XSearchResults(posts=[]) # Ensure data field exists for next step
            else:
                 # Ensure data is the Pydantic model instance
                if not isinstance(x_search_result.data, XSearchResults):
                    x_search_result.data = XSearchResults(**x_search_result.data)

            self.logger.info(f"[X_PULSE_STEP2] SUCCESS. Posts found: {len(x_search_result.data.posts)}")
        except Exception as e:
            self.logger.error(f"[X_PULSE_STEP2] Exception: {str(e)}")
            x_search_result = AgentResult(success=False, error=str(e), agent_name=self.sub_agents[1].config.name, data=XSearchResults(posts=[]))
            results.append(x_search_result)
        
        # Step 3: Analyze themes from X posts
        theme_analysis_result: Optional[AgentResult] = None
        try:
            theme_agent = self.sub_agents[2]
            # Pass the Pydantic model XSearchResults directly
            theme_context = {**context, 'posts_data': x_search_result.data} 
            self.logger.info(f"[X_PULSE_STEP3] {session_id} - Starting {theme_agent.config.name}")
            theme_analysis_result = await theme_agent.execute(theme_context)
            results.append(theme_analysis_result)
            if not theme_analysis_result.success or not theme_analysis_result.data:
                self.logger.error(f"[X_PULSE_STEP3] FAILED: {theme_analysis_result.error}")
            else:
                if not isinstance(theme_analysis_result.data, SubAgentThemeList):
                    theme_analysis_result.data = SubAgentThemeList(**theme_analysis_result.data)
                self.logger.info(f"[X_PULSE_STEP3] SUCCESS. Themes identified: {len(theme_analysis_result.data.themes)}")
        except Exception as e:
            self.logger.error(f"[X_PULSE_STEP3] Exception: {str(e)}")
            results.append(AgentResult(success=False, error=str(e), agent_name=self.sub_agents[2].config.name))

        successful_steps = sum(1 for r in results if r.success)
        total_tokens = sum(r.tokens_used or 0 for r in results)
        total_time = int((datetime.now() - orchestration_start).total_seconds() * 1000)
        self.logger.info(
            f"[X_PULSE_ORCHESTRATION] {session_id} - COMPLETED | "
            f"Total time: {total_time}ms | "
            f"Successful steps: {successful_steps}/{num_sub_agents} | "
            f"Total tokens: {total_tokens}"
        )
        return results

    def _aggregate_results(self, results: List[AgentResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all sub-agents into a dictionary for post-processing."""
        # This method prepares data for the final _post_process LLM call
        # It converts sub-agent Pydantic models into a dictionary structure
        # that _post_process will use to build its prompt for generating XPulseAnalysis.
        
        aggregated_for_post_processing = {
            "keywords_used": [],
            "retrieved_posts_count": 0,
            "identified_themes_raw": [], # List of SubAgentTheme as dicts
            "data_caveats_initial": "Η ανάλυση αυτή αντικατοπτρίζει ένα στιγμιότυπο των συζητήσεων στο X και ενδέχεται να μην είναι αντιπροσωπευτική της ευρύτερης κοινής γνώμης ή επαληθευμένων γεγονότων."
        }

        if results and results[0].success and isinstance(results[0].data, KeywordExtractionResult):
            aggregated_for_post_processing["keywords_used"] = results[0].data.x_search_keywords
        
        if len(results) > 1 and results[1].success and isinstance(results[1].data, XSearchResults):
            aggregated_for_post_processing["retrieved_posts_count"] = len(results[1].data.posts)
            # Potentially pass some sample posts to the final aggregation step if needed for summary
            # For now, just passing count and themes.
            # We need to decide if the main XPulseAnalysis needs the raw posts from XSearchResults.
            # The schema for XPulseAnalysis.discussion_themes.representative_posts expects XPost models.
            # This mapping should happen here or in _post_process.

        if len(results) > 2 and results[2].success and isinstance(results[2].data, SubAgentThemeList):
            aggregated_for_post_processing["identified_themes_raw"] = [
                theme.model_dump() for theme in results[2].data.themes
            ]
            
        return aggregated_for_post_processing

    async def _post_process(self, aggregated_data_dict: Dict, model: ModelType, context: Dict[str, Any]) -> Dict:
        """
        Generate the final XPulseAnalysis object using an LLM call.
        The `aggregated_data_dict` contains outputs from sub-agents.
        This method is responsible for the final LLM call that shapes the XPulseAnalysis output.
        """
        # This is where the main XPulseAgent uses an LLM, so it should use structured output.
        # The prompt will take the aggregated_data_dict and ask the LLM to fill the XPulseAnalysis schema.

        raw_themes = aggregated_data_dict.get("identified_themes_raw", [])
        keywords_used = aggregated_data_dict.get("keywords_used", [])
        
        # Map sentiment strings to Enum + create XPost objects
        # This logic might be complex for a simple prompt, so LLM assistance is good.
        prompt_themes_input = []
        for raw_theme in raw_themes:
            prompt_themes_input.append(
                f"Theme Title: {raw_theme.get('theme_title', 'N/A')}\n"
                f"Theme Summary: {raw_theme.get('theme_summary', 'N/A')}\n"
                f"Representative Examples: {'; '.join(raw_theme.get('representative_examples', []))}\n"
                f"Stated Sentiment: {raw_theme.get('sentiment_label', 'Neutral')}\n"
            )
        themes_input_str = "\n---\n".join(prompt_themes_input)

        # Fields for XPulseAnalysis:
        # overall_discourse_summary: str
        # total_posts_analyzed: int (approximate)
        # discussion_themes: List[DiscussionTheme]
        #   DiscussionTheme: theme_title, theme_summary, sentiment (Enum), representative_posts (List[XPost]), prevalence
        # trending_hashtags: Optional[List[str]]
        # overall_sentiment: Sentiment (Enum)
        # key_influencers: Optional[List[str]] (anonymized)
        # data_caveats: str

        # Constructing the prompt for the final XPulseAnalysis generation
        # This is a complex prompt that asks the LLM to synthesize inputs into the final schema.
        final_prompt = f"""Based on the preceding analysis of X (Twitter) discussions related to keywords "{', '.join(keywords_used)}":
Raw Identified Themes from Sub-Analysis:
{themes_input_str if themes_input_str else "No specific themes were identified."}

Please synthesize this information and structure it according to the 'XPulseAnalysis' schema.
Your task is to generate the complete XPulseAnalysis object.
Specifically, determine the following fields:

1.  **overall_discourse_summary**: Provide an executive summary of the X discourse (max 500 chars).
2.  **total_posts_analyzed**: Estimate the total number of posts analyzed (e.g., based on initial search count: {aggregated_data_dict.get('retrieved_posts_count',0)}).
3.  **discussion_themes**: For each raw theme identified above, transform it into a structured 'DiscussionTheme'. This involves:
    *   `theme_title`: Use or refine the provided title.
    *   `theme_summary`: Use or refine the provided summary.
    *   `sentiment`: Convert the stated sentiment (e.g., "{Sentiment.POSITIVE.value}", "{Sentiment.NEGATIVE.value}", "{Sentiment.NEUTRAL.value}", "{Sentiment.MIXED.value}") into the correct enum value.
    *   `representative_posts`: For each representative example string, create an `XPost` object. You may need to infer `author_description` (e.g., "User"), `engagement_level` (e.g., "Medium"), and `timestamp_relative` (e.g., "Recently") if not detailed. Content should be the example string.
    *   `prevalence`: Estimate theme prevalence (e.g., "Κυρίαρχο", "Συχνό", "Μέτριο", "Σπάνιο").
4.  **trending_hashtags**: List any relevant trending hashtags (up to 10) if evident from themes or keywords.
5.  **overall_sentiment**: Determine the overall sentiment of the discourse from the available options: "{Sentiment.POSITIVE.value}", "{Sentiment.NEGATIVE.value}", "{Sentiment.NEUTRAL.value}", "{Sentiment.MIXED.value}".
6.  **key_influencers**: (Optional) List any key voices or influencer types (anonymized) if patterns emerge.
7.  **data_caveats**: Include the provided caveat: "{aggregated_data_dict.get('data_caveats_initial')}" and add any other relevant limitations.

Ensure the entire output is a valid JSON object matching the XPulseAnalysis schema. All text content must be in Greek.
"""
        self.logger.info(f"Attempting final XPulseAnalysis generation with prompt of length: {len(final_prompt)}")
        
        # This is the main LLM call for XPulseAgent that produces the final structured output.
        # For this to work, the base `NestedAgent` would need to support `response_model` for its `_post_process` step,
        # or this logic needs to be part of the `AnalysisAgent`'s `execute` flow.
        # Let's assume we make a direct structured call here, similar to how `_call_grok_structured` works in `AnalysisAgent`.
        
        try:
            # This is a conceptual call. The actual mechanism for a nested agent to call LLM
            # with structured output for its post-processing needs to be defined.
            # We'll mimic the structure of _call_grok_structured.
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()}, # NestedAgent needs _get_system_prompt
                {"role": "user", "content": final_prompt}
            ]

            response = await self.grok_client.async_client.beta.chat.completions.parse(
                model=model.value, # Model selected for XPulseAgent
                messages=messages,
                response_format=XPulseAnalysis, # Target schema for the entire output
                temperature=0.7 # Default from guide
            )
            
            parsed_result = response.choices[0].message.parsed # This is an XPulseAnalysis instance
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            self.logger.info(f"XPulseAgent post-processing successful, tokens: {tokens_used}")
            return {'data': parsed_result.model_dump(), 'tokens_used': tokens_used} # Return dict as per current base_agent

        except Exception as e:
            self.logger.error(f"Error in XPulseAgent post-processing LLM call: {str(e)}")
            # Fallback: try to return at least the aggregated data if full structuring fails
            return {
                'data': {
                    "overall_discourse_summary": "Σφάλμα κατά την τελική επεξεργασία των δεδομένων X Pulse.",
                    "discussion_themes": [], # Cannot provide themes if structuring failed
                    "total_posts_analyzed": aggregated_data_dict.get('retrieved_posts_count',0),
                    "trending_hashtags": [],
                    "overall_sentiment": Sentiment.NEUTRAL, # Default
                    "key_influencers": [],
                    "data_caveats": aggregated_data_dict.get('data_caveats_initial')
                }, 
                'tokens_used': 0
            }

    # Add _get_system_prompt for NestedAgent if it's making LLM calls in _post_process
    def _get_system_prompt(self) -> str:
        return "You are a sophisticated AI assistant responsible for analyzing and summarizing X (Twitter) discourse based on provided sub-analyses."