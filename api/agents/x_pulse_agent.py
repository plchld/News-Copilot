"""X Pulse Agent - Analyzes X (Twitter) discourse with nested sub-agents"""

from typing import Dict, Any, List, Optional
from .base_agent import NestedAgent, AnalysisAgent, AgentConfig, ModelType, ComplexityLevel, AgentResult
import asyncio
import json


class KeywordExtractorAgent(AnalysisAgent):
    """Sub-agent for extracting keywords from article"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'KeywordExtractorAgent':
        config = AgentConfig(
            name="KeywordExtractorAgent",
            description="Extracts keywords for X search",
            default_model=ModelType.GROK_3_MINI,  # Sub-agent uses mini
            complexity=ComplexityLevel.SIMPLE,
            timeout_seconds=30
        )
        
        def build_prompt(context):
            return f"""Analyze the provided news article text.
Identify and extract the following:
1. Main Topic: A concise phrase describing the core subject of the article.
2. Key Entities: A list of important people, organizations, locations, or specific terms mentioned.
3. Search Keywords: A list of 3-5 keywords or short phrases suitable for searching for related discussions on X (Twitter). Prioritize terms that are likely to yield relevant public discourse in Greek.

Article Text:
{context['article_text'][:2000]}...  # Limit to first 2000 chars for efficiency
"""
        
        def build_schema():
            return {
                "type": "object",
                "properties": {
                    "main_topic": {"type": "string", "description": "Core subject of the article."},
                    "key_entities": {"type": "array", "items": {"type": "string"}},
                    "x_search_keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["main_topic", "key_entities", "x_search_keywords"]
            }
        
        return cls(config, grok_client, build_prompt, build_schema)


class XSearchAgent(AnalysisAgent):
    """Sub-agent for searching X posts"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'XSearchAgent':
        config = AgentConfig(
            name="XSearchAgent",
            description="Searches and filters X posts",
            default_model=ModelType.GROK_3_MINI,  # Sub-agent uses mini
            complexity=ComplexityLevel.MEDIUM,
            timeout_seconds=60
        )
        
        def build_prompt(context):
            keywords = context.get('keywords', [])
            keyword_str = ", ".join(keywords)
            return f"""Search X (Twitter) for discussions related to these keywords: {keyword_str}
Focus on Greek language posts.
Find and summarize the most relevant and substantive posts.
Group similar posts by theme or viewpoint."""
        
        def build_schema():
            return {
                "type": "object",
                "properties": {
                    "posts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "theme": {"type": "string"},
                                "relevance": {"type": "string", "enum": ["high", "medium", "low"]}
                            }
                        }
                    }
                }
            }
        
        return cls(config, grok_client, build_prompt, build_schema)
    
    def _build_search_params(self, context: Dict[str, Any]) -> Optional[Dict]:
        """Build X-specific search parameters"""
        keywords = context.get('keywords', [])
        search_query = " OR ".join(keywords) + " lang:el"
        
        return {
            "mode": "on",
            "sources": [{"type": "x"}],
            "return_citations": True,
            "max_search_results": 30
        }


class ThemeAnalyzerAgent(AnalysisAgent):
    """Sub-agent for identifying discussion themes"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'ThemeAnalyzerAgent':
        config = AgentConfig(
            name="ThemeAnalyzerAgent",
            description="Identifies discussion themes from X posts",
            default_model=ModelType.GROK_3,  # Theme analysis needs grok-3
            complexity=ComplexityLevel.HIGH,
            timeout_seconds=90
        )
        
        def build_prompt(context):
            posts = context.get('posts', [])
            posts_text = "\n".join([f"- {p.get('content', '')}" for p in posts[:50]])
            
            return f"""Analyze these X posts and identify 3-5 dominant themes or distinct viewpoints.
For each theme provide:
1. A concise title (2-5 words)
2. A 1-2 sentence summary
3. Representative examples from the posts
4. The general sentiment around this theme

Posts to analyze:
{posts_text}

All output must be in Greek."""
        
        def build_schema():
            return {
                "type": "object",
                "properties": {
                    "themes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "theme_title": {"type": "string"},
                                "theme_summary": {"type": "string"},
                                "representative_examples": {"type": "array", "items": {"type": "string"}},
                                "sentiment": {"type": "string"}
                            }
                        }
                    }
                }
            }
        
        return cls(config, grok_client, build_prompt, build_schema)


class SentimentAnalyzerAgent(AnalysisAgent):
    """Sub-agent for analyzing sentiment per theme"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'SentimentAnalyzerAgent':
        config = AgentConfig(
            name="SentimentAnalyzerAgent",
            description="Analyzes sentiment for each theme",
            default_model=ModelType.GROK_3_MINI,  # Sub-agent uses mini
            complexity=ComplexityLevel.MEDIUM,
            timeout_seconds=45
        )
        
        def build_prompt(context):
            themes = context.get('themes', [])
            return f"""For each theme, analyze the overall sentiment and tone of the discussion.
Classify as: Έντονη κριτική, Θετική υποδοχή, Μικτές αντιδράσεις, Ενημερωτική συζήτηση, etc.
Provide brief justification for each classification.
All output in Greek."""
        
        def build_schema():
            return {
                "type": "object",
                "properties": {
                    "sentiment_analysis": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "theme": {"type": "string"},
                                "sentiment": {"type": "string"},
                                "justification": {"type": "string"}
                            }
                        }
                    }
                }
            }
        
        return cls(config, grok_client, build_prompt, build_schema)


class XPulseAgent(NestedAgent):
    """Main X Pulse agent that coordinates sub-agents"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'XPulseAgent':
        """Factory method to create a configured XPulseAgent with sub-agents"""
        config = AgentConfig(
            name="XPulseAgent",
            description="Analyzes X discourse using nested agents",
            default_model=ModelType.GROK_3,  # Main coordinator uses grok-3
            complexity=ComplexityLevel.VERY_HIGH,
            supports_streaming=True,
            timeout_seconds=180
        )
        
        # Create sub-agents
        sub_agents = [
            KeywordExtractorAgent.create(grok_client),
            XSearchAgent.create(grok_client),
            ThemeAnalyzerAgent.create(grok_client),
            SentimentAnalyzerAgent.create(grok_client)
        ]
        
        return cls(config, grok_client, sub_agents)
    
    async def _execute_sub_agents(self, context: Dict[str, Any]) -> List[AgentResult]:
        """Custom orchestration for X Pulse sub-agents"""
        results = []
        
        # Step 1: Extract keywords
        keyword_result = await self.sub_agents[0].execute(context)
        results.append(keyword_result)
        
        if not keyword_result.success:
            return results
        
        # Step 2: Search X with extracted keywords
        search_context = {
            **context,
            'keywords': keyword_result.data.get('x_search_keywords', [])
        }
        search_result = await self.sub_agents[1].execute(search_context)
        results.append(search_result)
        
        if not search_result.success:
            return results
        
        # Step 3 & 4: Analyze themes and sentiment in parallel
        posts_context = {
            **context,
            'posts': search_result.data.get('posts', [])
        }
        
        theme_task = self.sub_agents[2].execute(posts_context)
        sentiment_task = self.sub_agents[3].execute(posts_context)
        
        theme_result, sentiment_result = await asyncio.gather(theme_task, sentiment_task)
        results.extend([theme_result, sentiment_result])
        
        return results
    
    def _aggregate_results(self, results: List[AgentResult], context: Dict[str, Any]) -> Dict:
        """Aggregate results from all sub-agents"""
        aggregated = {
            "overall_discourse_summary": "",
            "discussion_themes": [],
            "data_caveats": "Η ανάλυση αυτή αντικατοπτρίζει ένα στιγμιότυπο των συζητήσεων στο X και ενδέχεται να μην είναι αντιπροσωπευτική της ευρύτερης κοινής γνώμης ή επαληθευμένων γεγονότων."
        }
        
        # Extract data from each successful sub-agent
        if len(results) > 0 and results[0].success:  # Keywords
            keywords = results[0].data.get('x_search_keywords', [])
            aggregated['keywords_used'] = keywords
        
        if len(results) > 2 and results[2].success:  # Themes
            themes = results[2].data.get('themes', [])
            aggregated['discussion_themes'] = themes
        
        if len(results) > 3 and results[3].success:  # Sentiment
            sentiment_data = results[3].data.get('sentiment_analysis', [])
            # Merge sentiment data with themes
            for i, theme in enumerate(aggregated['discussion_themes']):
                if i < len(sentiment_data):
                    theme['sentiment_around_theme'] = sentiment_data[i].get('sentiment', '')
        
        return aggregated
    
    async def _post_process(self, aggregated_data: Dict, model: ModelType, 
                           context: Dict[str, Any]) -> Dict:
        """Generate overall discourse summary using main model"""
        themes = aggregated_data.get('discussion_themes', [])
        if not themes:
            aggregated_data['overall_discourse_summary'] = "Δεν βρέθηκαν επαρκείς συζητήσεις στο X για αυτό το θέμα."
            return {'data': aggregated_data, 'tokens_used': 0}
        
        # Create summary prompt
        themes_text = "\n".join([f"- {t.get('theme_title', '')}: {t.get('theme_summary', '')}" 
                                for t in themes])
        
        summary_prompt = f"""Based on these themes from X discussions:
{themes_text}

Provide a 2-3 sentence overall summary of the X discourse in Greek.
Focus on the main trends and public sentiment."""
        
        try:
            response = await self.grok_client.create_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                model=model.value
            )
            
            summary = response.choices[0].message.content
            aggregated_data['overall_discourse_summary'] = summary
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {'data': aggregated_data, 'tokens_used': tokens_used}
            
        except Exception as e:
            self.logger.error(f"Error in X Pulse post-processing: {str(e)}")
            aggregated_data['overall_discourse_summary'] = "Σφάλμα κατά τη δημιουργία σύνοψης."
            return {'data': aggregated_data, 'tokens_used': 0}