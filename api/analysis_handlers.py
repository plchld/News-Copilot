"""
Analysis handlers module for News Copilot
Contains the core analysis logic for different types of article analysis
"""
import json
import time
from typing import Dict, Any, Generator, List
from pydantic import BaseModel

from .article_extractor import fetch_text
from .grok_client import GrokClient
from .models import TermExplanation, JargonResponse

# Import prompts from the parent directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from prompts import (
    GROK_CONTEXT_JARGON_PROMPT_SCHEMA,
    GROK_ALTERNATIVE_VIEWPOINTS_PROMPT
)
# Import new prompt utilities
from .prompt_utils import (
    build_prompt,
    get_fact_check_task_instruction,
    get_bias_analysis_task_instruction,
    get_timeline_task_instruction,
    get_expert_opinions_task_instruction,
    get_article_topic_extraction_instruction,
    get_x_pulse_analysis_task_instruction,
    get_fact_check_schema,
    get_bias_analysis_schema,
    get_timeline_schema,
    get_expert_opinions_schema,
    get_article_topic_extraction_schema,
    get_x_pulse_analysis_schema
)


class AnalysisHandler:
    """Handler for all article analysis operations"""
    
    def __init__(self):
        self.grok_client = GrokClient()
        # Initialize agent coordinator for concurrent execution
        try:
            from .agents.coordinator import AgentCoordinator, CoordinatorConfig
        except ImportError:
            # Fallback for direct execution
            from agents.coordinator import AgentCoordinator, CoordinatorConfig
        config = CoordinatorConfig(
            max_parallel_agents=4,  # Allow concurrent execution
            enable_streaming=False,  # We handle streaming at this level
            timeout_seconds=120,
            retry_failed_agents=True
        )
        self.coordinator = AgentCoordinator(self.grok_client, config)
        
    def stream_event(self, event_type: str, data: Any) -> str:
        """Format a server-sent event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    async def get_augmentations_stream(self, article_url: str) -> Generator[str, None, None]:
        """
        Stream article augmentations (jargon explanations and alternative viewpoints).
        
        Args:
            article_url: URL of the article to analyze
            
        Yields:
            Server-sent events with progress updates and results
        """
        print(f"[get_augmentations_stream] Starting for URL: {article_url}", flush=True)
        yield self.stream_event("progress", {"status": "Initializing analysis..."})
        
        # Fetch article text
        article_text = None
        try:
            print("[get_augmentations_stream] Calling fetch_text...", flush=True)
            yield self.stream_event("progress", {"status": "Fetching article content..."})
            article_text = fetch_text(article_url)
            print(f"[get_augmentations_stream] fetch_text returned article_text (length: {len(article_text)})", flush=True)
            yield self.stream_event("progress", {"status": f"Article extracted ({len(article_text)} characters)"})
        except RuntimeError as e:
            print(f"[get_augmentations_stream] ERROR from fetch_text: {e}", flush=True)
            yield self.stream_event("error", {"message": f"Error fetching article: {str(e)}"})
            return
        except Exception as e:
            print(f"[get_augmentations_stream] UNEXPECTED ERROR: {e}", flush=True)
            yield self.stream_event("error", {"message": "Unexpected error fetching article."})
            return
        
        # Prepare search parameters with domain exclusion
        from urllib.parse import urlparse
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '')  # Remove www prefix if present
        print(f"[get_augmentations_stream] Excluding current article domain from search: {article_domain}", flush=True)
        
        search_params = self.grok_client.get_default_search_params()
        
        # Add excluded websites for the current article domain
        if 'sources' in search_params:
            for source in search_params['sources']:
                if source.get('type') in ['web', 'news']:
                    if 'excluded_websites' not in source:
                        source['excluded_websites'] = []
                    if article_domain not in source['excluded_websites']:
                        source['excluded_websites'].append(article_domain)
        
        # Use agent coordinator for concurrent jargon + viewpoints execution
        try:
            print("[get_augmentations_stream] Starting concurrent jargon + viewpoints analysis...", flush=True)
            yield self.stream_event("progress", {"status": "🚀 Starting concurrent analysis..."})
            
            # Import agent types
            try:
                from .agents.coordinator import AnalysisType
            except ImportError:
                from agents.coordinator import AnalysisType
            
            # Build context for agents
            context = {
                'article_url': article_url,
                'article_text': article_text,
                'user_tier': 'free',  # Default tier for basic analysis
                'user_id': 'basic_analysis'
            }
            
            # Execute jargon and viewpoints agents concurrently
            yield self.stream_event("progress", {"status": "🧠 Analyzing terms & finding viewpoints in parallel..."})
            
            results = await self.coordinator.analyze_article(
                article_url=article_url,
                article_text=article_text,
                analysis_types=[AnalysisType.JARGON, AnalysisType.VIEWPOINTS],
                user_context=context
            )
            
            print(f"[get_augmentations_stream] Concurrent analysis completed! Results: {list(results.keys())}", flush=True)
            
            # Extract results and format for frontend compatibility
            final_results = {"jargon": None, "jargon_citations": [], "viewpoints": None, "viewpoints_citations": []}
            
            # Process jargon results
            if AnalysisType.JARGON in results and results[AnalysisType.JARGON].success:
                jargon_result = results[AnalysisType.JARGON]
                final_results["jargon"] = jargon_result.data
                final_results["jargon_citations"] = []  # Agent system handles citations differently
                print(f"[get_augmentations_stream] Jargon analysis successful in {jargon_result.execution_time_ms}ms", flush=True)
            else:
                error = results.get(AnalysisType.JARGON, {}).error if AnalysisType.JARGON in results else "Agent not executed"
                print(f"[get_augmentations_stream] Jargon analysis failed: {error}", flush=True)
                yield self.stream_event("error", {"message": "Error explaining terms."})
                return
            
            # Process viewpoints results
            if AnalysisType.VIEWPOINTS in results and results[AnalysisType.VIEWPOINTS].success:
                viewpoints_result = results[AnalysisType.VIEWPOINTS]
                final_results["viewpoints"] = viewpoints_result.data
                final_results["viewpoints_citations"] = []  # Agent system handles citations differently
                print(f"[get_augmentations_stream] Viewpoints analysis successful in {viewpoints_result.execution_time_ms}ms", flush=True)
            else:
                error = results.get(AnalysisType.VIEWPOINTS, {}).error if AnalysisType.VIEWPOINTS in results else "Agent not executed"
                print(f"[get_augmentations_stream] Viewpoints analysis failed: {error}", flush=True)
                yield self.stream_event("error", {"message": "Error finding viewpoints."})
                return
            
            # Calculate total performance improvement
            total_time = max(
                results.get(AnalysisType.JARGON, {}).execution_time_ms or 0,
                results.get(AnalysisType.VIEWPOINTS, {}).execution_time_ms or 0
            )
            sequential_time = (results.get(AnalysisType.JARGON, {}).execution_time_ms or 0) + \
                            (results.get(AnalysisType.VIEWPOINTS, {}).execution_time_ms or 0)
            
            if sequential_time > 0:
                speedup = sequential_time / total_time if total_time > 0 else 1
                print(f"[PERFORMANCE] Concurrent execution speedup: {speedup:.1f}x faster ({sequential_time}ms → {total_time}ms)", flush=True)
            
            yield self.stream_event("progress", {"status": "✅ Concurrent analysis complete!"})
            
        except Exception as e:
            error_message = f"Error during concurrent analysis: {type(e).__name__} - {e}"
            print(f"[get_augmentations_stream] ERROR: {error_message}", flush=True)
            yield self.stream_event("error", {"message": "Error during analysis."})
            return
        
        print(f"[get_augmentations_stream] All tasks complete. Sending final results.", flush=True)
        yield self.stream_event("progress", {"status": "Analysis complete!"})
        yield self.stream_event("final_result", final_results)
    
    def get_deep_analysis(self, article_url: str, analysis_type: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep analysis using Grok API with specific prompts for each analysis type.
        
        Args:
            article_url: URL of the article to analyze
            analysis_type: Type of analysis ('fact-check', 'bias', 'timeline', 'expert')
            search_params: Search parameters for the API
            
        Returns:
            Dictionary with analysis results and citations
        """
        print(f"[get_deep_analysis] Starting {analysis_type} analysis for URL: {article_url}", flush=True)
        
        # Fetch article text
        article_text = fetch_text(article_url)
        print(f"[get_deep_analysis] Fetched article_text (first 500 chars): {article_text[:500]}", flush=True)
        
        # Map analysis types to instruction generators and schemas
        instruction_map = {
            'fact-check': (get_fact_check_task_instruction, get_fact_check_schema),
            'bias': (get_bias_analysis_task_instruction, get_bias_analysis_schema),
            'timeline': (get_timeline_task_instruction, get_timeline_schema),
            'expert': (get_expert_opinions_task_instruction, get_expert_opinions_schema),
            'x-pulse': (None, get_x_pulse_analysis_schema)  # Special handling below
        }
        
        if analysis_type not in instruction_map:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        # Handle X Pulse specially - it needs topic extraction first
        if analysis_type == 'x-pulse':
            # First, extract topics and keywords
            topic_instruction = get_article_topic_extraction_instruction(article_text)
            topic_schema = get_article_topic_extraction_schema()
            topic_prompt = build_prompt(topic_instruction, topic_schema)
            
            # Use thinking model for topic extraction
            topic_completion = self.grok_client.create_thinking_completion(
                prompt=topic_prompt,
                reasoning_effort="low",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            topic_data = json.loads(topic_completion.choices[0].message.content)
            main_topic = topic_data.get('main_topic', '')
            keywords = topic_data.get('x_search_keywords', [])
            
            print(f"[get_deep_analysis] X-Pulse topic extraction: topic='{main_topic}', keywords={keywords}", flush=True)
            
            # Now create the X Pulse instruction with extracted data
            task_instruction = get_x_pulse_analysis_task_instruction(article_text, main_topic, keywords)
            schema = get_x_pulse_analysis_schema()
            prompt_content = build_prompt(task_instruction, schema)
        else:
            # Regular analysis types
            instruction_fn, schema_fn = instruction_map[analysis_type]
            
            # Generate task instruction
            task_instruction = instruction_fn(article_text)
            
            # Build complete prompt with hardened template
            schema = schema_fn()
            prompt_content = build_prompt(task_instruction, schema)
        
        # Import search params builder and preset functions
        from .search_params_builder import (
            build_search_params, 
            get_search_params_for_x_pulse,
            get_search_params_for_fact_check,
            get_search_params_for_bias_analysis,
            get_search_params_for_timeline,
            get_search_params_for_expert_opinions
        )
        from urllib.parse import urlparse
        
        # Extract domain from article URL to exclude it from search results
        parsed_url = urlparse(article_url)
        article_domain = parsed_url.netloc.replace('www.', '')  # Remove www prefix if present
        print(f"[get_deep_analysis] Excluding current article domain from search: {article_domain}", flush=True)
        
        # Build search parameters using the builder
        # If searchParams provided by client, use them, otherwise use defaults
        if analysis_type == 'x-pulse':
            # Use specialized X Pulse search params
            search_params_dict = get_search_params_for_x_pulse(
                mode="on",
                keywords=keywords if 'keywords' in locals() else None,
                article_domain=article_domain
            )
        elif search_params:
            # Extract relevant fields from client searchParams
            # Merge excluded websites with article domain
            excluded_map = search_params.get("excluded_websites_map", {})
            if not excluded_map:
                excluded_map = {"web": [], "news": []}
            else:
                # Make a copy to avoid modifying the original
                excluded_map = dict(excluded_map)
                if "web" not in excluded_map:
                    excluded_map["web"] = []
                if "news" not in excluded_map:
                    excluded_map["news"] = []
            
            # Add article domain to both web and news exclusions
            if article_domain not in excluded_map["web"]:
                excluded_map["web"].append(article_domain)
            if article_domain not in excluded_map["news"]:
                excluded_map["news"].append(article_domain)
            
            search_params_dict = build_search_params(
                mode=search_params.get("mode", "on"),
                sources=search_params.get("sources"),
                country=search_params.get("country", "GR"),
                language=search_params.get("language", "el"),
                include_english=search_params.get("include_english", False),
                from_date=search_params.get("from_date"),
                to_date=search_params.get("to_date"),
                max_results=search_params.get("max_results", 20),
                safe_search=search_params.get("safe_search", True),
                excluded_websites_map=excluded_map,
                x_handles_for_x_source=search_params.get("x_handles_for_x_source"),
                rss_links_for_rss_source=search_params.get("rss_links_for_rss_source")
            )
        else:
            # Use preset search params based on analysis type
            preset_map = {
                'fact-check': get_search_params_for_fact_check,
                'bias': get_search_params_for_bias_analysis,
                'timeline': get_search_params_for_timeline,
                'expert': get_search_params_for_expert_opinions
            }
            
            if analysis_type in preset_map:
                # Use the appropriate preset function with article domain exclusion
                search_params_dict = preset_map[analysis_type](mode="on", article_domain=article_domain)
            else:
                # Fallback to default search params with article domain excluded
                search_params_dict = self.grok_client.get_default_search_params()
                
                # Add excluded websites for the current article domain
                if 'sources' in search_params_dict:
                    for source in search_params_dict['sources']:
                        if source.get('type') in ['web', 'news']:
                            if 'excluded_websites' not in source:
                                source['excluded_websites'] = []
                            if article_domain not in source['excluded_websites']:
                                source['excluded_websites'].append(article_domain)
        
        # Make API call with the schema already included in prompt
        completion = self.grok_client.create_completion(
            prompt=prompt_content,
            search_params=search_params_dict,
            response_format={"type": "json_object"},
            stream=False
        )
        
        if analysis_type == 'fact-check':
            print(f"[get_deep_analysis] RAW Grok 'fact-check' response content: {completion.choices[0].message.content}", flush=True)

        print(f"[get_deep_analysis] Grok {analysis_type} call successful.", flush=True)
        
        # Parse response
        response_data = json.loads(completion.choices[0].message.content)
        citations = self.grok_client.extract_citations(completion)
        
        # Special validation for expert analysis
        if analysis_type == 'expert':
            # Import citation processor
            from .citation_processor import validate_citations
            
            # Validate that experts mentioned actually appear in citations
            is_valid, issues = validate_citations(response_data, citations)
            if not is_valid:
                print(f"[get_deep_analysis] Expert validation issues: {issues}", flush=True)
                
            # Filter out experts without matching citations
            if 'experts' in response_data:
                validated_experts = []
                for expert in response_data['experts']:
                    # Check if expert name or opinion appears in any citation content
                    expert_found = False
                    expert_name = expert.get('name', '').lower()
                    
                    # For now, include all experts but log if they're not in citations
                    if not expert_found and expert_name:
                        print(f"[get_deep_analysis] Warning: Expert '{expert_name}' not found in citations", flush=True)
                    
                    validated_experts.append(expert)
                
                response_data['experts'] = validated_experts
        
        return {
            'analysis': response_data,
            'citations': citations,
            'analysis_type': analysis_type
        }
    
    def _get_analysis_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get JSON schemas for each analysis type"""
        return {
            'fact-check': {
                "type": "object",
                "properties": {
                    "overall_credibility": {"type": "string"},
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string"},
                                "verified": {"type": "boolean"},
                                "explanation": {"type": "string"},
                                "sources": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "red_flags": {"type": "array", "items": {"type": "string"}},
                    "missing_context": {"type": "string"}
                }
            },
            'bias': {
                "type": "object",
                "properties": {
                    "political_spectrum_analysis_greek": {
                        "type": "object",
                        "properties": {
                            "economic_axis_placement": {"type": "string"},
                            "economic_axis_justification": {"type": "string"},
                            "social_axis_placement": {"type": "string"},
                            "social_axis_justification": {"type": "string"},
                            "overall_confidence": {"type": "string"}
                        }
                    },
                    "language_and_framing_analysis": {
                        "type": "object",
                        "properties": {
                            "emotionally_charged_terms": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "term": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }
                            },
                            "identified_framing_techniques": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "technique_name": {"type": "string"},
                                        "example_from_article": {"type": "string"}
                                    }
                                }
                            },
                            "detected_tone": {"type": "string"},
                            "missing_perspectives_summary": {"type": "string"}
                        }
                    },
                    "sources_diversity": {"type": "string"},
                    "analysis_summary": {"type": "string"},
                    "supporting_evidence": {"type": "array", "items": {"type": "string"}}
                }
            },
            'timeline': {
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
                                "importance": {"type": "string"},
                                "source": {"type": "string"}
                            }
                        }
                    },
                    "context": {"type": "string"},
                    "future_implications": {"type": "string"}
                }
            },
            'expert': {
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
                                "stance": {"type": "string"}
                            }
                        }
                    },
                    "consensus": {"type": "string"},
                    "key_debates": {"type": "string"}
                }
            },
            'x-pulse': {
                "type": "object",
                "properties": {
                    "overall_discourse_summary": {"type": "string"},
                    "discussion_themes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "theme_title": {"type": "string"},
                                "theme_summary": {"type": "string"},
                                "representative_posts": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "post_content": {"type": "string"},
                                            "post_source_description": {"type": "string"}
                                        }
                                    }
                                },
                                "sentiment_around_theme": {"type": "string"}
                            }
                        }
                    },
                    "data_caveats": {"type": "string"}
                }
            }
        }