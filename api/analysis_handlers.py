"""
Analysis handlers module for News Copilot
Contains the core analysis logic for different types of article analysis
"""
import json
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
    get_fact_check_schema,
    get_bias_analysis_schema,
    get_timeline_schema,
    get_expert_opinions_schema
)


class AnalysisHandler:
    """Handler for all article analysis operations"""
    
    def __init__(self):
        self.grok_client = GrokClient()
        
    def stream_event(self, event_type: str, data: Any) -> str:
        """Format a server-sent event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    def get_augmentations_stream(self, article_url: str) -> Generator[str, None, None]:
        """
        Stream article augmentations (jargon explanations and alternative viewpoints).
        
        Args:
            article_url: URL of the article to analyze
            
        Yields:
            Server-sent events with progress updates and results
        """
        print(f"[get_augmentations_stream] Starting for URL: {article_url}", flush=True)
        yield self.stream_event("progress", {"status": "Initializing augmentation..."})
        
        # Fetch article text
        article_text = None
        try:
            print("[get_augmentations_stream] Calling fetch_text...", flush=True)
            yield self.stream_event("progress", {"status": "Fetching article content..."})
            article_text = fetch_text(article_url)
            print(f"[get_augmentations_stream] fetch_text returned article_text (length: {len(article_text)})", flush=True)
            yield self.stream_event("progress", {"status": f"Article content fetched ({len(article_text)} chars)."})
        except RuntimeError as e:
            print(f"[get_augmentations_stream] ERROR from fetch_text: {e}", flush=True)
            yield self.stream_event("error", {"message": f"Error fetching article: {str(e)}"})
            return
        except Exception as e:
            print(f"[get_augmentations_stream] UNEXPECTED ERROR: {e}", flush=True)
            yield self.stream_event("error", {"message": "Unexpected error fetching article."})
            return
        
        # Prepare search parameters
        search_params = self.grok_client.get_default_search_params()
        final_results = {"jargon": None, "jargon_citations": [], "viewpoints": None, "viewpoints_citations": []}
        
        # Get jargon explanations
        try:
            print("[get_augmentations_stream] Preparing for Grok jargon call...", flush=True)
            yield self.stream_event("progress", {"status": "Explaining terms and concepts..."})
            
            jargon_prompt = GROK_CONTEXT_JARGON_PROMPT_SCHEMA + "\n\nΆρθρο:\n" + article_text
            json_schema = JargonResponse.model_json_schema()
            
            jargon_completion = self.grok_client.create_completion(
                prompt=jargon_prompt,
                search_params=search_params,
                response_format={"type": "json_object", "schema": json_schema},
                stream=False
            )
            
            print("[get_augmentations_stream] Grok jargon call successful.", flush=True)
            
            if jargon_completion.choices[0].message.content:
                final_results["jargon"] = json.loads(jargon_completion.choices[0].message.content)
            
            final_results["jargon_citations"] = self.grok_client.extract_citations(jargon_completion)
            yield self.stream_event("progress", {"status": "Terms explained."})
            
        except Exception as e:
            error_message = f"Error during jargon analysis: {type(e).__name__} - {e}"
            print(f"[get_augmentations_stream] ERROR (jargon): {error_message}", flush=True)
            yield self.stream_event("error", {"message": "Error explaining terms."})
            return
        
        # Get alternative viewpoints
        try:
            print("[get_augmentations_stream] Preparing for Grok viewpoints call...", flush=True)
            yield self.stream_event("progress", {"status": "Finding alternative viewpoints..."})
            
            viewpoints_prompt = GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + "\n\nΠρωτότυπο Άρθρο για контекст:\n" + article_text
            
            viewpoints_completion = self.grok_client.create_completion(
                prompt=viewpoints_prompt,
                search_params=search_params,
                stream=False
            )
            
            print("[get_augmentations_stream] Grok viewpoints call successful.", flush=True)
            
            final_results["viewpoints"] = viewpoints_completion.choices[0].message.content
            final_results["viewpoints_citations"] = self.grok_client.extract_citations(viewpoints_completion)
            
            yield self.stream_event("progress", {"status": "Alternative viewpoints found."})
            
        except Exception as e:
            error_message = f"Error during viewpoints analysis: {type(e).__name__} - {e}"
            print(f"[get_augmentations_stream] ERROR (viewpoints): {error_message}", flush=True)
            yield self.stream_event("error", {"message": "Error finding viewpoints."})
            return
        
        print(f"[get_augmentations_stream] All tasks complete. Sending final results.", flush=True)
        yield self.stream_event("final_result", final_results)
        yield self.stream_event("progress", {"status": "Done!"})
    
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
            'expert': (get_expert_opinions_task_instruction, get_expert_opinions_schema)
        }
        
        if analysis_type not in instruction_map:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        # Get instruction generator and schema
        instruction_fn, schema_fn = instruction_map[analysis_type]
        
        # Generate task instruction
        task_instruction = instruction_fn(article_text)
        
        # Build complete prompt with hardened template
        schema = schema_fn()
        prompt_content = build_prompt(task_instruction, schema)
        
        # Import search params builder
        from .search_params_builder import build_search_params
        
        # Build search parameters using the builder
        # If searchParams provided by client, use them, otherwise use defaults
        if search_params:
            # Extract relevant fields from client searchParams
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
                excluded_websites_map=search_params.get("excluded_websites_map"),
                x_handles_for_x_source=search_params.get("x_handles_for_x_source"),
                rss_links_for_rss_source=search_params.get("rss_links_for_rss_source")
            )
        else:
            # Use default search params
            search_params_dict = self.grok_client.get_default_search_params()
        
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
                    "political_lean": {"type": "string"},
                    "confidence": {"type": "string"},
                    "emotional_tone": {"type": "string"},
                    "language_analysis": {
                        "type": "object",
                        "properties": {
                            "loaded_words": {"type": "array", "items": {"type": "string"}},
                            "framing": {"type": "string"},
                            "missing_perspectives": {"type": "string"}
                        }
                    },
                    "comparison": {"type": "string"},
                    "recommendations": {"type": "string"}
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
            }
        }