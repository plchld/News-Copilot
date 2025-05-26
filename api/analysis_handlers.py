"""
Analysis handlers module for News Copilot
Contains the core analysis logic for different types of article analysis
"""
import json
import time
from typing import Dict, Any, Generator, List
from pydantic import BaseModel

try:
    from .article_extractor import fetch_text
    from .grok_client import GrokClient
    from .models import TermExplanation, JargonResponse
except ImportError:
    from article_extractor import fetch_text
    from grok_client import GrokClient
    from models import TermExplanation, JargonResponse

# Import prompts from the parent directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from prompts import (
    GROK_CONTEXT_JARGON_PROMPT_SCHEMA,
    GROK_ALTERNATIVE_VIEWPOINTS_PROMPT
)
# Import new prompt utilities
try:
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
except ImportError:
    from prompt_utils import (
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
            from .agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
        except ImportError:
            # Fallback for direct execution
            from agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
        config = CoordinatorConfig(
            core_parallel_limit=2,  # Jargon + viewpoints
            core_timeout_seconds=150,  # Increased for viewpoints live search
            on_demand_timeout_seconds=120,
            cache_ttl_minutes=60,
            enable_result_caching=True,
            enable_context_caching=True
        )
        self.coordinator = AgentCoordinator(self.grok_client, config)
    
    async def _run_concurrent_analysis(self, article_url: str, article_text: str, context: Dict[str, Any]) -> Dict:
        """Helper method to run concurrent analysis"""
        try:
            from .agents.optimized_coordinator import AnalysisType
        except ImportError:
            from agents.optimized_coordinator import AnalysisType
        
        return await self.coordinator.analyze_core(
            article_url=article_url,
            article_text=article_text,
            user_context=context
        )
        
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
                from .agents.optimized_coordinator import AnalysisType
            except ImportError:
                from agents.optimized_coordinator import AnalysisType
            
            # Build context for agents
            context = {
                'article_url': article_url,
                'article_text': article_text,
                'user_tier': 'free',  # Default tier for basic analysis
                'user_id': 'basic_analysis'
            }
            
            # Execute jargon and viewpoints agents concurrently
            yield self.stream_event("progress", {"status": "🧠 Analyzing terms & finding viewpoints in parallel..."})
            
            # Now use the agent coordinator directly (async is fixed)
            results = await self.coordinator.analyze_core(
                article_url=article_url,
                article_text=article_text,
                user_context=context
            )
            
            print(f"[get_augmentations_stream] Concurrent analysis completed! Results: {list(results.keys())}", flush=True)
            
            # Extract results and format for frontend compatibility
            final_results = {"jargon": None, "jargon_citations": [], "viewpoints": None, "viewpoints_citations": []}
            
            # Check if core analysis was successful
            if not results.get('success'):
                error_msg = results.get('error', 'Core analysis failed')
                print(f"[get_augmentations_stream] Core analysis failed: {error_msg}", flush=True)
                yield self.stream_event("error", {"message": "Error during analysis."})
                return
            
            # Process results from the new structure
            core_results = results.get('results', {})
            errors = results.get('errors', {})
            
            # Process jargon results
            if core_results.get('jargon'):
                final_results["jargon"] = core_results['jargon']
                final_results["jargon_citations"] = []  # Agent system handles citations differently
                print(f"[get_augmentations_stream] Jargon analysis successful", flush=True)
            else:
                error = errors.get('jargon', 'Jargon analysis failed')
                print(f"[get_augmentations_stream] Jargon analysis failed: {error}", flush=True)
                yield self.stream_event("error", {"message": "Error explaining terms."})
                return
            
            # Process viewpoints results
            if core_results.get('viewpoints'):
                final_results["viewpoints"] = core_results['viewpoints']
                final_results["viewpoints_citations"] = []  # Agent system handles citations differently
                print(f"[get_augmentations_stream] Viewpoints analysis successful", flush=True)
            else:
                error = errors.get('viewpoints', 'Viewpoints analysis failed')
                print(f"[get_augmentations_stream] Viewpoints analysis failed: {error}", flush=True)
                yield self.stream_event("error", {"message": "Error finding viewpoints."})
                return
            
            # Log performance metrics
            metadata = results.get('metadata', {})
            execution_time = metadata.get('execution_time_seconds', 0)
            total_tokens = metadata.get('total_tokens_used', 0)
            successful_analyses = metadata.get('successful_analyses', 0)
            
            print(f"[PERFORMANCE] Core analysis completed in {execution_time:.2f}s | "
                  f"Success: {successful_analyses}/2 | Tokens: {total_tokens}", flush=True)
            
            yield self.stream_event("progress", {"status": "✅ Concurrent analysis complete!"})
            
        except Exception as e:
            error_message = f"Error during concurrent analysis: {type(e).__name__} - {e}"
            print(f"[get_augmentations_stream] ERROR: {error_message}", flush=True)
            yield self.stream_event("error", {"message": "Error during analysis."})
            return
        
        print(f"[get_augmentations_stream] All tasks complete. Sending final results.", flush=True)
        yield self.stream_event("progress", {"status": "Analysis complete!"})
        yield self.stream_event("final_result", final_results)

    async def get_deep_analysis(self, article_url: str, analysis_type: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep analysis using the OptimizedAgentCoordinator for structured outputs.
        
        Args:
            article_url: URL of the article to analyze
            analysis_type: Type of analysis ('fact-check', 'bias', 'timeline', 'expert', 'x-pulse')
            search_params: Client-provided search parameters to be passed in context (optional).
            
        Returns:
            Dictionary with analysis results. Citations are currently returned as an empty list.
        """
        print(f"[get_deep_analysis] Starting AGENT-BASED {analysis_type} analysis for URL: {article_url}", flush=True)
        
        # Fetch article text
        try:
            article_text = fetch_text(article_url)
            if not article_text:
                print(f"[get_deep_analysis] Error: Fetched empty article text for {article_url}", flush=True)
                # Consider raising an error or returning a specific error structure
                raise ValueError("Failed to fetch article content or content is empty.")
            print(f"[get_deep_analysis] Fetched article_text (length {len(article_text)})", flush=True)
        except Exception as e:
            print(f"[get_deep_analysis] Error fetching article text for {article_url}: {e}", flush=True)
            # Propagate error or return specific error structure
            raise # Or return an error dict

        # Import AnalysisType enum from the coordinator's module
        try:
            from .agents.optimized_coordinator import AnalysisType
        except ImportError:
            from agents.optimized_coordinator import AnalysisType # Fallback for direct execution

        # Map client-facing analysis_type string to AnalysisType enum
        analysis_type_map = {
            'fact-check': AnalysisType.FACT_CHECK,
            'bias': AnalysisType.BIAS_ANALYSIS,
            'timeline': AnalysisType.TIMELINE,
            'expert': AnalysisType.EXPERT_OPINIONS,
            'x-pulse': AnalysisType.X_PULSE
        }
        
        agent_type_enum = analysis_type_map.get(analysis_type)
        
        if agent_type_enum is None:
            print(f"[get_deep_analysis] Error: Unknown analysis type '{analysis_type}'", flush=True)
            raise ValueError(f"Unknown analysis type: {analysis_type}")

        # Prepare context for the agent coordinator
        # User tier and ID can be configurable or based on actual user session if available
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': 'premium', # Assuming deep analysis implies premium features
            'user_id': 'deep_analysis_user', # Generic user ID for this handler
            'session_id': f"deep_analysis_{analysis_type}_{time.time()}", # Unique session ID
            'search_params_override': search_params if search_params else None # Pass client search_params
        }
        
        print(f"[get_deep_analysis] Calling coordinator.analyze_on_demand for {agent_type_enum.name} with context.", flush=True)
        
        try:
            agent_result = await self.coordinator.analyze_on_demand(agent_type_enum, context)
        except Exception as e:
            print(f"[get_deep_analysis] Error during coordinator.analyze_on_demand for {agent_type_enum.name}: {e}", flush=True)
            raise 

        if not agent_result.success:
            error_message = agent_result.error or "Unknown error from agent."
            print(f"[get_deep_analysis] Agent {agent_type_enum.name} execution failed: {error_message}", flush=True)
            raise Exception(f"Analysis failed for {analysis_type}: {error_message}")

        print(f"[get_deep_analysis] Agent {agent_type_enum.name} execution successful.", flush=True)
        
        analysis_data = agent_result.data

        # Apply transformations for specific analysis types to match UI expectations
        if agent_result.success and analysis_data:
            if analysis_type == 'fact-check':
                analysis_data = transform_fact_check_for_ui(analysis_data)
                print(f"[get_deep_analysis] Applied 'fact-check' UI transformation.", flush=True)
            elif analysis_type == 'bias':
                analysis_data = transform_bias_for_ui(analysis_data)
                print(f"[get_deep_analysis] Applied 'bias' UI transformation.", flush=True)
        
        return {
            'analysis': analysis_data,
            'citations': [],  # Citations to be handled separately or by agents directly if needed
            'analysis_type': analysis_type
        }

# --- UI Transformation Functions ---

def transform_fact_check_for_ui(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms FactCheckAnalysis data (from Pydantic model_dump()) to the UI expected format.
    """
    ui_claims = []
    if agent_data.get("claims"):
        for claim_data in agent_data["claims"]:
            verdict_str = claim_data.get("verdict", "")
            # Mapping based on api.agents.schemas.Verdict enum string values
            verified = verdict_str in ["Αληθές", "Κυρίως Αληθές"]
            
            ui_claim = {
                "statement": claim_data.get("claim"),
                "verified": verified,
                "explanation": claim_data.get("explanation"),
                "sources": [source.get("url") for source in claim_data.get("sources", []) if source.get("url")]
            }
            ui_claims.append(ui_claim)

    return {
        "overall_credibility": agent_data.get("overall_credibility"),
        "claims": ui_claims,
        "red_flags": agent_data.get("red_flags", []),
        "missing_context": agent_data.get("missing_context"),
        "source_quality": None # Not available in FactCheckAnalysis schema
    }

def transform_bias_for_ui(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms BiasAnalysis data (from Pydantic model_dump()) to the UI expected format.
    """
    objectivity_score = agent_data.get("objectivity_score")
    confidence = None
    if isinstance(objectivity_score, (int, float)):
        if 8 <= objectivity_score <= 10:
            confidence = "High"
        elif 4 <= objectivity_score <= 7:
            confidence = "Medium"
        elif 1 <= objectivity_score <= 3:
            confidence = "Low"

    bias_indicators = agent_data.get("bias_indicators", [])
    framing_elements = [ind.get("indicator") for ind in bias_indicators if ind.get("indicator")]
    loaded_words_elements = [ind.get("example") for ind in bias_indicators if ind.get("example")]

    missing_perspectives_list = agent_data.get("missing_perspectives", [])
    missing_perspectives_str = ", ".join(missing_perspectives_list) if missing_perspectives_list else None

    return {
        "political_lean": agent_data.get("political_leaning"), # Assuming enum value is string
        "emotional_tone": None, # Not directly available in BiasAnalysis schema
        "confidence": confidence,
        "language_analysis": {
            "framing": ", ".join(framing_elements) if framing_elements else None,
            "loaded_words": loaded_words_elements,
            "missing_perspectives": missing_perspectives_str
        },
        "comparison": None, # Not available in BiasAnalysis schema
        "recommendations": None, # Not available in BiasAnalysis schema
        # Including objectivity_score and reasoning directly if UI can use them,
        # or they can be omitted if only the transformed fields above are needed.
        "objectivity_score_raw": objectivity_score, 
        "reasoning_raw": agent_data.get("reasoning")
    }

    # This method is now obsolete as schemas are defined by Pydantic models within agents
    # and prompt building is handled by agents.
    # def _get_analysis_schemas(self) -> Dict[str, Dict[str, Any]]:
    # Keeping it commented out for now, to be deleted in a subsequent step as per instructions.
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