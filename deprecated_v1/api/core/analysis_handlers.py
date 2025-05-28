"""
Analysis handlers module for News Copilot
Contains the core analysis logic for different types of article analysis
"""
import json
import time
from typing import Dict, Any, Generator, List
from pydantic import BaseModel
import logging

from .article_extractor import fetch_text
from .grok_client import GrokClient
from ..models import TermExplanation, JargonResponse
from ..agents.base_agent import AgentResult, ModelType
from ..agents.jargon_agent import JargonAgent

# Import prompts from the root directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from prompts import (
    GROK_CONTEXT_JARGON_PROMPT_SCHEMA,
    GROK_ALTERNATIVE_VIEWPOINTS_PROMPT
)
# Import new prompt utilities
try:
    from utils.prompt_utils import (
        build_prompt,
        get_jargon_task_instruction,
        get_jargon_response_schema,
        get_alt_view_task_instruction,
        get_alternative_viewpoints_schema,
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
    from ..utils.prompt_utils import (
        build_prompt,
        get_jargon_task_instruction,
        get_jargon_response_schema,
        get_alt_view_task_instruction,
        get_alternative_viewpoints_schema,
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
            from ..agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
        except ImportError:
            try:
                # Alternative import path
                from api.agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
            except ImportError:
                # Fallback for direct execution
                from agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
        config = CoordinatorConfig(
            core_parallel_limit=2,  # Jargon + viewpoints
            core_timeout_seconds=150,  # Increased for viewpoints live search
            on_demand_timeout_seconds=120,
            cache_ttl_minutes=60,
            enable_result_caching=False,  # Disabled caching
            enable_context_caching=False  # Disabled caching
        )
        self.coordinator = AgentCoordinator(self.grok_client, config)
    
    async def _run_concurrent_analysis(self, article_url: str, article_text: str, context: Dict[str, Any]) -> Dict:
        """Helper method to run concurrent analysis"""
        try:
            from ..agents.optimized_coordinator import AnalysisType
        except ImportError:
            try:
                from api.agents.optimized_coordinator import AnalysisType
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
    
    def get_augmentations_stream(self, article_url: str) -> Generator[str, None, None]:
        """
        Stream article augmentations using async coordinator with sync wrapper.
        
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
        
        # Use the optimized coordinator for core analysis
        try:
            print("[get_augmentations_stream] Starting core analysis with coordinator...", flush=True)
            yield self.stream_event("progress", {"status": "🚀 Starting core analysis (jargon + viewpoints)..."})
            
            # Build user context
            user_context = {
                'user_tier': 'free',  # Default for basic streaming
                'user_id': 'basic_analysis'
            }
            
            # Run async coordinator in sync context
            import asyncio
            
            async def run_core_analysis():
                return await self.coordinator.analyze_core(
                    article_url=article_url,
                    article_text=article_text,
                    user_context=user_context
                )
            
            # Execute async function in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, use thread executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, run_core_analysis())
                        result = future.result(timeout=180)  # 3 minute timeout
                else:
                    result = loop.run_until_complete(run_core_analysis())
            except RuntimeError:
                # No event loop, create one
                result = asyncio.run(run_core_analysis())
            
            print(f"[get_augmentations_stream] Core analysis result: {result.get('success', False)}", flush=True)
            
            if result.get('success'):
                core_results = result.get('results', {})
                
                # Stream jargon results if available
                if 'jargon' in core_results and core_results['jargon']:
                    yield self.stream_event("jargon", core_results['jargon'])
                    yield self.stream_event("progress", {"status": "✅ Terms explained!"})
                else:
                    yield self.stream_event("error", {"message": "Error explaining terms."})
                
                # Stream viewpoints results if available  
                if 'viewpoints' in core_results and core_results['viewpoints']:
                    yield self.stream_event("viewpoints", core_results['viewpoints'])
                    yield self.stream_event("progress", {"status": "✅ Alternative viewpoints found!"})
                else:
                    yield self.stream_event("error", {"message": "Error finding viewpoints."})
                
                # Final completion
                successful_count = sum(1 for k in ['jargon', 'viewpoints'] if core_results.get(k))
                yield self.stream_event("progress", {"status": f"✅ Analysis complete! ({successful_count}/2 successful)"})
            else:
                error_msg = result.get('error', 'Core analysis failed')
                print(f"[get_augmentations_stream] Core analysis failed: {error_msg}", flush=True)
                yield self.stream_event("error", {"message": error_msg})
                return
                
        except Exception as e:
            error_message = f"Error during core analysis: {type(e).__name__} - {e}"
            print(f"[get_augmentations_stream] ERROR: {error_message}", flush=True)
            yield self.stream_event("error", {"message": "Error during analysis."})
            return
    
    def process_deep_analysis(self, article_url: str, analysis_type: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep analysis using the agent framework for consistency.
        
        Args:
            article_url: URL of the article to analyze
            analysis_type: Type of analysis ('fact-check', 'bias', 'timeline', 'expert')
            search_params: Search parameters for the API
            
        Returns:
            Dictionary with analysis results and citations
        """
        print(f"[process_deep_analysis] Starting {analysis_type} analysis for URL: {article_url}", flush=True)
        
        # Use the agent framework for markdown-based analyses
        if analysis_type in ['fact-check', 'jargon', 'viewpoints']:
            import asyncio
            from datetime import datetime
            
            # Fetch article text once
            article_text = fetch_text(article_url)
            
            # Build user context with all required fields for non-cached operation
            user_context = {
                'article_url': article_url,
                'article_text': article_text,
                'user_tier': 'free',
                'session_id': f"deep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self):x}",
                'search_params': search_params,
                'user_id': 'deep_analysis'  # Add user_id for consistency
            }
            
            # Use selective analysis for single type
            result = self.process_selective_analysis(
                article_url=article_url,
                analysis_types=[analysis_type],
                user_context=user_context
            )
            
            if result.get('success') and result.get('results', {}).get(analysis_type):
                # Return in the expected format
                return {
                    'analysis': result['results'][analysis_type],
                    'citations': [],  # Agent framework handles citations internally
                    'analysis_type': analysis_type
                }
            else:
                error_msg = result.get('errors', {}).get(analysis_type, 'Analysis failed')
                raise RuntimeError(error_msg)
        
        # Continue with original implementation for non-markdown analyses
        print(f"[process_deep_analysis] Using direct API call for {analysis_type}")
        
        # Fetch article text
        article_text = fetch_text(article_url)
        print(f"[process_deep_analysis] Fetched article_text (first 500 chars): {article_text[:500]}", flush=True)
        
        # Map analysis types to instruction generators and schemas
        instruction_map = {
            'jargon': (get_jargon_task_instruction, get_jargon_response_schema),
            'viewpoints': (get_alt_view_task_instruction, get_alternative_viewpoints_schema),
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
            # Note: Grok doesn't support response_format parameter
            topic_completion = self.grok_client.create_thinking_completion(
                prompt=topic_prompt,
                reasoning_effort="low",
                temperature=0.3
            )
            
            topic_data = json.loads(topic_completion.choices[0].message.content)
            main_topic = topic_data.get('main_topic', '')
            keywords = topic_data.get('x_search_keywords', [])
            
            print(f"[process_deep_analysis] X-Pulse topic extraction: topic='{main_topic}', keywords={keywords}", flush=True)
            
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
        from ..utils.search_params_builder import (
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
        print(f"[process_deep_analysis] Excluding current article domain from search: {article_domain}", flush=True)
        
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
        # Note: Grok doesn't support response_format parameter
        try:
            completion = self.grok_client.create_completion(
                prompt=prompt_content,
                search_params=search_params_dict,
                stream=False
            )
        except Exception as grok_error:
            error_msg = f"Grok API call failed for {analysis_type}: {str(grok_error)}"
            print(f"[process_deep_analysis] {error_msg}", flush=True)
            raise RuntimeError(error_msg)
        
        if analysis_type == 'fact-check':
            print(f"[process_deep_analysis] RAW Grok 'fact-check' response content: {completion.choices[0].message.content}", flush=True)

        print(f"[process_deep_analysis] Grok {analysis_type} call successful.", flush=True)
        
        # Parse response with error handling
        try:
            if not completion.choices or not completion.choices[0].message or not completion.choices[0].message.content:
                raise ValueError(f"Empty response from Grok API for {analysis_type}")
            
            response_content = completion.choices[0].message.content.strip()
            if not response_content:
                raise ValueError(f"Empty content in Grok response for {analysis_type}")
            
            response_data = json.loads(response_content)
            
            # Validate response structure
            if not isinstance(response_data, dict):
                raise ValueError(f"Invalid response format from Grok API for {analysis_type}: expected dict, got {type(response_data)}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response for {analysis_type}: {str(e)}"
            print(f"[process_deep_analysis] {error_msg}", flush=True)
            print(f"[process_deep_analysis] Raw response content: {completion.choices[0].message.content[:500]}...", flush=True)
            raise RuntimeError(error_msg)
        except Exception as parse_error:
            error_msg = f"Error processing response for {analysis_type}: {str(parse_error)}"
            print(f"[process_deep_analysis] {error_msg}", flush=True)
            raise RuntimeError(error_msg)
        
        # Extract citations with error handling
        try:
            citations = self.grok_client.extract_citations(completion)
        except Exception as citation_error:
            print(f"[process_deep_analysis] Warning: Failed to extract citations for {analysis_type}: {citation_error}", flush=True)
            citations = []
        
        # Special validation for expert analysis
        if analysis_type == 'expert':
            # Import citation processor
            from .citation_processor import validate_citations
            
            # Validate that experts mentioned actually appear in citations
            is_valid, issues = validate_citations(response_data, citations)
            if not is_valid:
                print(f"[process_deep_analysis] Expert validation issues: {issues}", flush=True)
                
            # Filter out experts without matching citations
            if 'experts' in response_data:
                validated_experts = []
                for expert in response_data['experts']:
                    # Check if expert name or opinion appears in any citation content
                    expert_found = False
                    expert_name = expert.get('name', '').lower()
                    
                    # For now, include all experts but log if they're not in citations
                    if not expert_found and expert_name:
                        print(f"[process_deep_analysis] Warning: Expert '{expert_name}' not found in citations", flush=True)
                    
                    validated_experts.append(expert)
                
                response_data['experts'] = validated_experts
        
        return {
            'analysis': response_data,
            'citations': citations,
            'analysis_type': analysis_type
        }
    
    def process_selective_analysis(self, article_url: str, analysis_types: List[str], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multiple selected analysis types concurrently using the optimized coordinator.
        
        Args:
            article_url: URL of the article to analyze
            analysis_types: List of analysis types to execute
            user_context: User context including tier, API key, etc.
            
        Returns:
            Dictionary with results, metadata, and errors for each analysis type
        """
        import asyncio
        import time
        from datetime import datetime
        
        print(f"[process_selective_analysis] Starting selective analysis: {analysis_types} for URL: {article_url}", flush=True)
        
        # Fetch article text once for all analyses
        try:
            article_text = fetch_text(article_url)
            print(f"[process_selective_analysis] Fetched article_text (length: {len(article_text)})", flush=True)
        except Exception as e:
            error_msg = f"Error fetching article: {str(e)}"
            print(f"[process_selective_analysis] {error_msg}", flush=True)
            return {
                'success': False,
                'error': error_msg,
                'results': {},
                'metadata': {},
                'errors': {t: error_msg for t in analysis_types}
            }
        
        # Separate core and on-demand analyses
        core_types = ['jargon', 'viewpoints']
        on_demand_types = ['fact-check', 'bias', 'timeline', 'expert', 'x-pulse']
        
        selected_core = [t for t in analysis_types if t in core_types]
        selected_on_demand = [t for t in analysis_types if t in on_demand_types]
        
        print(f"[process_selective_analysis] Core types: {selected_core}, On-demand types: {selected_on_demand}", flush=True)
        
        # Build enhanced user context
        # Use existing session_id if provided, otherwise create new one
        session_id = user_context.get('session_id') or f"selective_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self):x}"
        
        enhanced_context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': user_context.get('user_tier', 'free'),
            'user_id': user_context.get('user_id'),
            'session_id': session_id,
            **user_context
        }
        
        results = {}
        metadata = {}
        errors = {}
        start_time = time.time()
        
        async def run_selective_analysis():
            session_id = enhanced_context['session_id']
            
            # Step 1: Run core analysis if needed (creates cache for on-demand analyses)
            if selected_core:
                print(f"[process_selective_analysis] Running core analysis: {selected_core}", flush=True)
                try:
                    core_result = await self.coordinator.analyze_core(
                        article_url=article_url,
                        article_text=article_text,
                        user_context=enhanced_context
                    )
                    
                    if core_result.get('success'):
                        core_results = core_result.get('results', {})
                        # Add successful core results with transformation
                        for analysis_type in selected_core:
                            if analysis_type in core_results and core_results[analysis_type]:
                                # Transform core analysis data for UI compatibility
                                transformed_result = self._transform_analysis_data(analysis_type, core_results[analysis_type])
                                results[analysis_type] = transformed_result
                                metadata[analysis_type] = {
                                    'execution_method': 'core_coordinator',
                                    'cached_for_on_demand': True
                                }
                            else:
                                errors[analysis_type] = f"Core analysis failed for {analysis_type}"
                    else:
                        # Core analysis failed
                        for analysis_type in selected_core:
                            errors[analysis_type] = core_result.get('error', 'Core analysis failed')
                    
                    # Update metadata with core analysis info
                    core_metadata = core_result.get('metadata', {})
                    metadata['core_analysis'] = core_metadata
                    
                except Exception as e:
                    error_msg = f"Core analysis error: {str(e)}"
                    print(f"[process_selective_analysis] {error_msg}", flush=True)
                    for analysis_type in selected_core:
                        errors[analysis_type] = error_msg
            
            # Step 2: Run on-demand analyses concurrently
            if selected_on_demand:
                print(f"[process_selective_analysis] Running on-demand analyses: {selected_on_demand}", flush=True)
                
                async def run_on_demand_analysis(analysis_type):
                    try:
                        result = await self.coordinator.analyze_on_demand(
                            analysis_type=analysis_type,
                            session_id=session_id,
                            user_context=enhanced_context
                        )
                        
                        if result.get('success'):
                            # Transform data for UI compatibility
                            raw_result = result.get('result')
                            transformed_result = self._transform_analysis_data(analysis_type, raw_result)
                            results[analysis_type] = transformed_result
                            metadata[analysis_type] = result.get('metadata', {})
                            metadata[analysis_type]['execution_method'] = 'on_demand_coordinator'
                        else:
                            errors[analysis_type] = result.get('error', f'{analysis_type} analysis failed')
                        
                        return analysis_type, result
                    except Exception as e:
                        error_msg = f"{analysis_type} analysis error: {str(e)}"
                        print(f"[process_selective_analysis] {error_msg}", flush=True)
                        errors[analysis_type] = error_msg
                        return analysis_type, {'success': False, 'error': error_msg}
                
                # Create tasks for all on-demand analyses
                on_demand_tasks = [
                    asyncio.create_task(run_on_demand_analysis(analysis_type))
                    for analysis_type in selected_on_demand
                ]
                
                # Wait for all on-demand analyses to complete
                try:
                    await asyncio.gather(*on_demand_tasks, return_exceptions=True)
                except Exception as e:
                    print(f"[process_selective_analysis] Error in on-demand gather: {e}", flush=True)
        
        # Run the async analysis
        try:
            # Handle event loop for different contexts
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, use thread executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, run_selective_analysis())
                        future.result()
                else:
                    loop.run_until_complete(run_selective_analysis())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(run_selective_analysis())
        except Exception as e:
            error_msg = f"Selective analysis execution error: {str(e)}"
            print(f"[process_selective_analysis] {error_msg}", flush=True)
            return {
                'success': False,
                'error': error_msg,
                'results': results,
                'metadata': metadata,
                'errors': {**errors, 'execution_error': error_msg}
            }
        
        # Calculate final metrics
        execution_time = time.time() - start_time
        successful_count = len(results)
        failed_count = len(errors)
        
        print(f"[process_selective_analysis] Completed in {execution_time:.2f}s | Success: {successful_count}/{len(analysis_types)} | Errors: {failed_count}", flush=True)
        
        return {
            'success': successful_count > 0,
            'results': results,
            'metadata': {
                'total_execution_time_seconds': execution_time,
                'successful_analyses': successful_count,
                'failed_analyses': failed_count,
                'requested_types': analysis_types,
                'execution_method': 'selective_analysis',
                **metadata
            },
            'errors': errors
        }
    
    def _transform_analysis_data(self, analysis_type: str, raw_data: Any) -> Any:
        """
        Transform backend analysis data to match UI expectations.
        
        Args:
            analysis_type: The type of analysis
            raw_data: Raw data from the backend
            
        Returns:
            Transformed data compatible with UI components
        """
        if not raw_data:
            return raw_data
            
        if analysis_type in ['fact-check', 'jargon', 'viewpoints']:
            # Return markdown data as-is
            return raw_data
        
        # For other analysis types, return as-is for now
        return raw_data
    
    def _transform_fact_check_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform fact-check data from backend schema to UI schema.
        
        Backend schema:
        - evidence_assessment: "ισχυρά τεκμηριωμένο", "μερικώς τεκμηριωμένο", etc.
        - context: explanation text
        - complexity_note: additional context
        
        UI schema:
        - verdict: 'TRUE', 'FALSE', 'MISLEADING', 'UNVERIFIABLE'
        - explanation: combined context
        """
        if not raw_data or 'claims' not in raw_data:
            return raw_data
        
        # Map Greek evidence assessments to English verdicts
        evidence_to_verdict_map = {
            "ισχυρά τεκμηριωμένο": "TRUE",           # strongly supported
            "μερικώς τεκμηριωμένο": "MISLEADING",     # partially supported
            "αμφιλεγόμενο": "MISLEADING",             # disputed/contested
            "ελλιπώς τεκμηριωμένο": "MISLEADING",     # poorly supported
            "χωρίς επαρκή στοιχεία": "UNVERIFIABLE",  # insufficient evidence
            "εκτός πλαισίου": "MISLEADING"            # out of context
        }
        
        transformed_claims = []
        for claim in raw_data['claims']:
            # Map evidence_assessment to verdict
            evidence_assessment = claim.get('evidence_assessment', '')
            verdict = evidence_to_verdict_map.get(evidence_assessment, 'UNVERIFIABLE')
            
            # Combine context and complexity_note for explanation
            explanation_parts = []
            if claim.get('context'):
                explanation_parts.append(claim['context'])
            if claim.get('complexity_note'):
                explanation_parts.append(f"**Επιπλέον σημείωση:** {claim['complexity_note']}")
            
            explanation = ' '.join(explanation_parts) if explanation_parts else 'Δεν υπάρχουν διαθέσιμες λεπτομέρειες.'
            
            # Transform sources to string array if they're objects
            sources = claim.get('sources', [])
            if sources and isinstance(sources[0], dict):
                # Extract description from source objects
                sources = [src.get('description', str(src)) for src in sources]
            elif not isinstance(sources, list):
                sources = []
            
            transformed_claim = {
                'claim': claim.get('claim', ''),
                'verdict': verdict,
                'explanation': explanation,
                'sources': sources
            }
            transformed_claims.append(transformed_claim)
        
        # Create overall credibility summary from source_quality if available
        overall_credibility = None
        if 'source_quality' in raw_data:
            source_quality = raw_data['source_quality']
            primary = source_quality.get('primary_sources', 0)
            secondary = source_quality.get('secondary_sources', 0)
            diversity = source_quality.get('source_diversity', 'άγνωστο')
            
            overall_credibility = f"Βασίστηκε σε {primary} πρωτογενείς και {secondary} δευτερογενείς πηγές. Ποικιλία πηγών: {diversity}."
        
        return {
            'claims': transformed_claims,
            'overall_credibility': overall_credibility
        }
    
    def _transform_jargon_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform jargon data from backend schema to UI schema.
        
        Backend schema:
        - source_mention: single source string
        
        UI schema:
        - sources: array of source strings
        """
        if not raw_data or 'terms' not in raw_data:
            return raw_data
        
        transformed_terms = []
        for term in raw_data['terms']:
            transformed_term = {
                'term': term.get('term', ''),
                'explanation': term.get('explanation', ''),
            }
            
            # Convert source_mention to sources array
            if term.get('source_mention'):
                transformed_term['sources'] = [term['source_mention']]
            
            transformed_terms.append(transformed_term)
        
        return {
            'terms': transformed_terms
        }
    
    def _transform_viewpoints_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform viewpoints data. Check if any transformation is needed.
        """
        # For now, return as-is - the viewpoints schema might already match UI expectations
        # If issues are found, add transformations here
        return raw_data
    
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


# Convenience function for backward compatibility
def stream_augmented_analysis(url: str, api_key: str = None):
    """
    Synchronous wrapper for streaming analysis.
    Creates handler and runs async analysis in event loop.
    """
    import asyncio
    
    handler = AnalysisHandler()
    
    # Create async generator wrapper
    async def async_generator():
        async for event in handler.get_augmentations_stream(url):
            yield event
    
    # Run async generator in event loop
    async def run_generator():
        results = []
        async for event in async_generator():
            results.append(event)
        return results
    
    # Handle event loop for different contexts
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_generator())
                events = future.result()
        else:
            events = loop.run_until_complete(run_generator())
    except RuntimeError:
        # No event loop, create one
        events = asyncio.run(run_generator())
    
    # Return generator that yields the events
    for event in events:
        yield event