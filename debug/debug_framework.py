"""
Agent Debugging Framework

Provides comprehensive debugging capabilities for the News-Copilot agent system.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from contextlib import asynccontextmanager

from .base_agent import BaseAgent, AgentResult
from .optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType


class DebugLevel(Enum):
    """Debug verbosity levels"""
    MINIMAL = "minimal"      # Basic success/failure
    NORMAL = "normal"        # Standard debugging info
    VERBOSE = "verbose"      # Detailed execution traces
    EXTREME = "extreme"      # Everything including API payloads


@dataclass
class ExecutionTrace:
    """Detailed trace of an agent execution"""
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    
    # Execution phases
    phases: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # API interactions
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Search parameters
    search_params: Optional[Dict] = None
    
    # Model selection
    model_used: Optional[str] = None
    model_selection_reason: Optional[str] = None
    
    # Performance metrics
    total_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    
    # Result data
    result_data: Optional[Dict] = None
    result_validation: Optional[str] = None
    
    def add_phase(self, phase_name: str, data: Dict[str, Any]):
        """Add execution phase data"""
        self.phases[phase_name] = {
            'timestamp': datetime.now(),
            'data': data
        }
    
    def add_api_call(self, request: Dict, response: Optional[Dict] = None, error: Optional[str] = None):
        """Record an API call"""
        self.api_calls.append({
            'timestamp': datetime.now(),
            'request': request,
            'response': response,
            'error': error
        })
    
    def finalize(self, success: bool, error: Optional[str] = None):
        """Finalize the trace"""
        self.end_time = datetime.now()
        self.success = success
        self.error = error
        if self.start_time and self.end_time:
            self.total_time_ms = int((self.end_time - self.start_time).total_seconds() * 1000)


class AgentDebugger:
    """Debug wrapper for agents with comprehensive tracing"""
    
    def __init__(self, agent: BaseAgent, debug_level: DebugLevel = DebugLevel.NORMAL):
        self.agent = agent
        self.debug_level = debug_level
        self.traces: List[ExecutionTrace] = []
        self.logger = logging.getLogger(f"AgentDebugger.{agent.config.name}")
        
    async def execute_with_trace(self, context: Dict[str, Any]) -> Tuple[AgentResult, ExecutionTrace]:
        """Execute agent with detailed tracing"""
        trace = ExecutionTrace(
            agent_name=self.agent.config.name,
            start_time=datetime.now()
        )
        
        try:
            # Hook into agent execution phases
            original_execute = self.agent.execute
            
            # Create instrumented version
            async def instrumented_execute(ctx):
                # Phase 1: Context preparation
                trace.add_phase("context_prep", {
                    'article_length': len(ctx.get('article_text', '')),
                    'user_tier': ctx.get('user_tier', 'free'),
                    'session_id': ctx.get('session_id', 'unknown')
                })
                
                # Hook model selection
                if hasattr(self.agent, 'select_model'):
                    original_select_model = self.agent.select_model
                    def traced_select_model(context):
                        model = original_select_model(context)
                        trace.model_used = model.value if hasattr(model, 'value') else str(model)
                        trace.add_phase("model_selection", {
                            'selected_model': trace.model_used,
                            'article_words': len(context.get('article_text', '').split()),
                            'retry_count': context.get('retry_count', 0)
                        })
                        return model
                    self.agent.select_model = traced_select_model
                
                # Hook search params building
                if hasattr(self.agent, '_build_search_params'):
                    original_build_search = self.agent._build_search_params
                    def traced_build_search(context):
                        params = original_build_search(context)
                        trace.search_params = params
                        trace.add_phase("search_params", {
                            'has_search': params is not None,
                            'sources': len(params.get('sources', [])) if params else 0,
                            'excluded_domains': len(params.get('excluded_websites_map', {}).get('domains', [])) if params else 0
                        })
                        return params
                    self.agent._build_search_params = traced_build_search
                
                # Hook API calls
                if hasattr(self.agent, '_call_grok'):
                    original_call_grok = self.agent._call_grok
                    async def traced_call_grok(prompt, schema, model, search_params, context):
                        api_start = datetime.now()
                        
                        # Record request (truncate if in non-extreme mode)
                        request_data = {
                            'model': model.value if hasattr(model, 'value') else str(model),
                            'prompt_length': len(prompt),
                            'has_search': search_params is not None,
                            'has_conversation': bool(context.get('conversation_history'))
                        }
                        
                        if self.debug_level == DebugLevel.EXTREME:
                            request_data['prompt'] = prompt[:1000]  # First 1000 chars
                            request_data['search_params'] = search_params
                            request_data['schema'] = schema
                        
                        trace.add_phase("api_call_start", request_data)
                        
                        try:
                            result = await original_call_grok(prompt, schema, model, search_params, context)
                            
                            api_time = int((datetime.now() - api_start).total_seconds() * 1000)
                            
                            # Record response
                            response_data = {
                                'success': True,
                                'api_time_ms': api_time,
                                'tokens_used': result.get('tokens_used', 0)
                            }
                            
                            if self.debug_level in [DebugLevel.VERBOSE, DebugLevel.EXTREME]:
                                response_data['data_keys'] = list(result.get('data', {}).keys())
                                
                            trace.add_api_call(request_data, response_data)
                            trace.tokens_used = result.get('tokens_used', 0)
                            
                            return result
                            
                        except Exception as e:
                            trace.add_api_call(request_data, error=str(e))
                            raise
                    
                    self.agent._call_grok = traced_call_grok
                
                # Execute with instrumentation
                result = await original_execute(ctx)
                
                # Record result
                trace.result_data = result.data if result.success else None
                trace.add_phase("execution_complete", {
                    'success': result.success,
                    'error': result.error,
                    'execution_time_ms': result.execution_time_ms
                })
                
                # Validate result content
                if result.success and result.data:
                    validation_info = self._validate_result_content(result.data)
                    trace.result_validation = validation_info
                    trace.add_phase("result_validation", {
                        'validation_status': validation_info,
                        'data_structure': {k: type(v).__name__ for k, v in result.data.items()}
                    })
                
                return result
            
            # Execute with instrumentation
            self.agent.execute = instrumented_execute
            result = await self.agent.execute(context)
            
            trace.finalize(success=result.success, error=result.error)
            self.traces.append(trace)
            
            return result, trace
            
        except Exception as e:
            trace.finalize(success=False, error=str(e))
            self.traces.append(trace)
            raise
    
    def _validate_result_content(self, data: Dict[str, Any]) -> str:
        """Validate and categorize result content"""
        if not data:
            return "EMPTY_DATA"
        
        empty_fields = []
        populated_fields = []
        
        for key, value in data.items():
            if isinstance(value, list):
                if len(value) == 0:
                    empty_fields.append(f"{key}(list)")
                else:
                    populated_fields.append(f"{key}({len(value)} items)")
            elif isinstance(value, str):
                if len(value.strip()) == 0:
                    empty_fields.append(f"{key}(str)")
                else:
                    populated_fields.append(f"{key}({len(value)} chars)")
            elif isinstance(value, dict):
                if len(value) == 0:
                    empty_fields.append(f"{key}(dict)")
                else:
                    populated_fields.append(f"{key}({len(value)} keys)")
            else:
                populated_fields.append(f"{key}({type(value).__name__})")
        
        if empty_fields and not populated_fields:
            return f"ALL_EMPTY: {', '.join(empty_fields)}"
        elif empty_fields:
            return f"PARTIAL_EMPTY: empty=[{', '.join(empty_fields)}], populated=[{', '.join(populated_fields)}]"
        else:
            return f"FULLY_POPULATED: {', '.join(populated_fields)}"
    
    def generate_report(self, trace: Optional[ExecutionTrace] = None) -> str:
        """Generate human-readable debug report"""
        if trace is None and self.traces:
            trace = self.traces[-1]  # Use most recent
        
        if not trace:
            return "No execution traces available"
        
        report = []
        report.append(f"\n{'='*80}")
        report.append(f"AGENT DEBUG REPORT: {trace.agent_name}")
        report.append(f"{'='*80}")
        
        # Basic info
        report.append(f"\nExecution Summary:")
        report.append(f"  Status: {'SUCCESS' if trace.success else 'FAILED'}")
        report.append(f"  Total Time: {trace.total_time_ms}ms")
        report.append(f"  Model Used: {trace.model_used or 'unknown'}")
        report.append(f"  Tokens Used: {trace.tokens_used or 0}")
        
        if trace.error:
            report.append(f"  Error: {trace.error}")
        
        # Execution phases
        report.append(f"\nExecution Phases:")
        for phase_name, phase_data in trace.phases.items():
            report.append(f"  {phase_name}:")
            for key, value in phase_data.get('data', {}).items():
                report.append(f"    - {key}: {value}")
        
        # Search parameters
        if trace.search_params:
            report.append(f"\nSearch Configuration:")
            report.append(f"  Sources: {len(trace.search_params.get('sources', []))}")
            report.append(f"  Max Results: {trace.search_params.get('max_results', 'default')}")
            excluded = trace.search_params.get('excluded_websites_map', {}).get('domains', [])
            if excluded:
                report.append(f"  Excluded Domains: {', '.join(excluded[:5])}{'...' if len(excluded) > 5 else ''}")
        
        # API calls
        if trace.api_calls:
            report.append(f"\nAPI Calls ({len(trace.api_calls)}):")
            for i, call in enumerate(trace.api_calls, 1):
                report.append(f"  Call {i}:")
                req = call.get('request', {})
                resp = call.get('response', {})
                
                report.append(f"    Model: {req.get('model', 'unknown')}")
                report.append(f"    Prompt Length: {req.get('prompt_length', 0)} chars")
                
                if resp:
                    report.append(f"    Response Time: {resp.get('api_time_ms', 'unknown')}ms")
                    report.append(f"    Tokens: {resp.get('tokens_used', 0)}")
                
                if call.get('error'):
                    report.append(f"    ERROR: {call['error']}")
        
        # Result validation
        if trace.result_validation:
            report.append(f"\nResult Validation:")
            report.append(f"  {trace.result_validation}")
        
        # Result data preview (if verbose)
        if self.debug_level in [DebugLevel.VERBOSE, DebugLevel.EXTREME] and trace.result_data:
            report.append(f"\nResult Data Preview:")
            for key, value in trace.result_data.items():
                if isinstance(value, list) and value:
                    report.append(f"  {key}: [{len(value)} items]")
                    if self.debug_level == DebugLevel.EXTREME:
                        # Show first item
                        first_item = str(value[0])[:200]
                        report.append(f"    First item: {first_item}{'...' if len(str(value[0])) > 200 else ''}")
                elif isinstance(value, str):
                    preview = value[:200]
                    report.append(f"  {key}: {preview}{'...' if len(value) > 200 else ''}")
                else:
                    report.append(f"  {key}: {type(value).__name__}")
        
        report.append(f"\n{'='*80}\n")
        
        return '\n'.join(report)


class CoordinatorDebugger:
    """Debug wrapper for AgentCoordinator with batch execution insights"""
    
    def __init__(self, coordinator: AgentCoordinator, debug_level: DebugLevel = DebugLevel.NORMAL):
        self.coordinator = coordinator
        self.debug_level = debug_level
        self.agent_debuggers: Dict[AnalysisType, AgentDebugger] = {}
        
        # Wrap all agents
        for analysis_type, agent in coordinator.agents.items():
            self.agent_debuggers[analysis_type] = AgentDebugger(agent, debug_level)
    
    async def execute_with_trace(
        self, 
        analysis_types: List[AnalysisType],
        context: Dict[str, Any],
        stream_callback: Optional[Any] = None
    ) -> Tuple[Dict[AnalysisType, AgentResult], Dict[AnalysisType, ExecutionTrace]]:
        """Execute coordinator with comprehensive tracing"""
        
        traces = {}
        results = {}
        
        # Hook into coordinator's agent execution
        original_execute_agent = self.coordinator._execute_agent_with_retry
        
        async def traced_execute_agent(agent, context, analysis_type):
            debugger = self.agent_debuggers.get(analysis_type)
            if debugger:
                result, trace = await debugger.execute_with_trace(context)
                traces[analysis_type] = trace
                return result
            else:
                # Fallback to original
                return await original_execute_agent(agent, context, analysis_type)
        
        self.coordinator._execute_agent_with_retry = traced_execute_agent
        
        # Execute
        if stream_callback:
            results = await self.coordinator.execute_streaming(analysis_types, context, stream_callback)
        else:
            results = await self.coordinator.execute(analysis_types, context)
        
        return results, traces
    
    def generate_batch_report(self, traces: Dict[AnalysisType, ExecutionTrace]) -> str:
        """Generate report for batch execution"""
        report = []
        report.append(f"\n{'='*80}")
        report.append(f"BATCH EXECUTION REPORT")
        report.append(f"{'='*80}")
        
        # Summary
        successful = sum(1 for t in traces.values() if t.success)
        total = len(traces)
        report.append(f"\nSummary: {successful}/{total} agents succeeded")
        
        # Timing analysis
        total_time = sum(t.total_time_ms or 0 for t in traces.values())
        report.append(f"Total Execution Time: {total_time}ms")
        
        # Individual agent summaries
        report.append(f"\nAgent Results:")
        for analysis_type, trace in traces.items():
            status = "✓" if trace.success else "✗"
            time_str = f"{trace.total_time_ms}ms" if trace.total_time_ms else "N/A"
            error_str = f" - {trace.error}" if trace.error else ""
            report.append(f"  {status} {analysis_type.value}: {time_str}{error_str}")
            
            # Add validation info if available
            if trace.result_validation:
                report.append(f"     → {trace.result_validation}")
        
        # Detailed reports for failed agents
        failed_traces = {k: v for k, v in traces.items() if not v.success}
        if failed_traces and self.debug_level != DebugLevel.MINIMAL:
            report.append(f"\nDetailed Failure Reports:")
            for analysis_type, trace in failed_traces.items():
                debugger = self.agent_debuggers.get(analysis_type)
                if debugger:
                    report.append(debugger.generate_report(trace))
        
        report.append(f"\n{'='*80}\n")
        
        return '\n'.join(report)


# Convenience functions
async def debug_single_agent(
    agent: BaseAgent,
    article_url: str,
    debug_level: DebugLevel = DebugLevel.VERBOSE
) -> Tuple[AgentResult, str]:
    """Debug a single agent execution"""
    from ..article_extractor import fetch_text
    
    # Extract article
    try:
        article_text = fetch_text(article_url)
    except Exception as e:
        raise ValueError(f"Failed to extract article: {str(e)}")
    
    # Prepare context
    context = {
        'article_text': article_text,
        'article_url': article_url,
        'session_id': f'debug_{datetime.now().timestamp()}',
        'user_tier': 'premium',  # Use premium for debugging
    }
    
    # Execute with debugging
    debugger = AgentDebugger(agent, debug_level)
    result, trace = await debugger.execute_with_trace(context)
    
    # Generate report
    report = debugger.generate_report(trace)
    
    return result, report


async def debug_agent_batch(
    coordinator: AgentCoordinator,
    analysis_types: List[AnalysisType],
    article_url: str,
    debug_level: DebugLevel = DebugLevel.NORMAL
) -> Tuple[Dict[AnalysisType, AgentResult], str]:
    """Debug a batch of agent executions"""
    from ..article_extractor import fetch_text
    
    # Extract article
    try:
        article_text = fetch_text(article_url)
    except Exception as e:
        raise ValueError(f"Failed to extract article: {str(e)}")
    
    # Prepare context
    context = {
        'article_text': article_text,
        'article_url': article_url,
        'session_id': f'debug_batch_{datetime.now().timestamp()}',
        'user_tier': 'premium',
    }
    
    # Execute with debugging
    debugger = CoordinatorDebugger(coordinator, debug_level)
    results, traces = await debugger.execute_with_trace(analysis_types, context)
    
    # Generate report
    report = debugger.generate_batch_report(traces)
    
    return results, report