"""Trace management for debugging agents"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SpanType(Enum):
    """Types of spans for tracing"""
    AGENT = "agent"
    GENERATION = "generation"
    FUNCTION_CALL = "function_call"
    SEARCH = "search"
    SYNTHESIS = "synthesis"
    ERROR = "error"
    CUSTOM = "custom"


@dataclass
class SpanData:
    """Data for a single span"""
    span_id: str
    span_type: SpanType
    name: str
    started_at: float
    ended_at: Optional[float] = None
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate span duration in seconds"""
        if self.ended_at is None:
            return None
        return self.ended_at - self.started_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "span_id": self.span_id,
            "span_type": self.span_type.value,
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration": self.duration,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "error": self.error
        }


@dataclass
class AgentTrace:
    """Complete trace for an agent workflow"""
    trace_id: str
    workflow_name: str
    started_at: float
    ended_at: Optional[float] = None
    spans: List[SpanData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate total trace duration"""
        if self.ended_at is None:
            return None
        return self.ended_at - self.started_at
    
    def add_span(self, span: SpanData):
        """Add a span to the trace"""
        self.spans.append(span)
    
    def get_spans_by_type(self, span_type: SpanType) -> List[SpanData]:
        """Get spans by type"""
        return [s for s in self.spans if s.span_type == span_type]
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get performance metrics for agents"""
        agent_spans = self.get_spans_by_type(SpanType.AGENT)
        generation_spans = self.get_spans_by_type(SpanType.GENERATION)
        
        return {
            "total_agents": len(agent_spans),
            "total_generations": len(generation_spans),
            "avg_agent_duration": sum(s.duration or 0 for s in agent_spans) / len(agent_spans) if agent_spans else 0,
            "avg_generation_duration": sum(s.duration or 0 for s in generation_spans) / len(generation_spans) if generation_spans else 0,
            "errors": len([s for s in self.spans if s.error]),
            "agents_used": list(set(s.metadata.get("agent_name", "unknown") for s in agent_spans))
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "workflow_name": self.workflow_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration": self.duration,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
            "performance": self.get_agent_performance()
        }


class TraceManager:
    """Manager for handling traces and spans"""
    
    def __init__(self, enabled: bool = True):
        """Initialize trace manager
        
        Args:
            enabled: Whether tracing is enabled
        """
        self.enabled = enabled
        self.active_traces: Dict[str, AgentTrace] = {}
        self.completed_traces: List[AgentTrace] = []
        self.current_trace_id: Optional[str] = None
        self.current_span_stack: List[str] = []  # Stack of active span IDs
    
    def create_trace(self, workflow_name: str, trace_id: Optional[str] = None) -> str:
        """Create a new trace
        
        Args:
            workflow_name: Name of the workflow
            trace_id: Optional custom trace ID
            
        Returns:
            Trace ID
        """
        if not self.enabled:
            return "disabled"
        
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
        
        trace = AgentTrace(
            trace_id=trace_id,
            workflow_name=workflow_name,
            started_at=time.time()
        )
        
        self.active_traces[trace_id] = trace
        self.current_trace_id = trace_id
        
        logger.debug(f"Created trace: {trace_id} for workflow: {workflow_name}")
        return trace_id
    
    def finish_trace(self, trace_id: Optional[str] = None) -> Optional[AgentTrace]:
        """Finish a trace
        
        Args:
            trace_id: Trace ID to finish (defaults to current)
            
        Returns:
            Completed trace or None
        """
        if not self.enabled:
            return None
        
        trace_id = trace_id or self.current_trace_id
        if not trace_id or trace_id not in self.active_traces:
            return None
        
        trace = self.active_traces.pop(trace_id)
        trace.ended_at = time.time()
        
        self.completed_traces.append(trace)
        
        if self.current_trace_id == trace_id:
            self.current_trace_id = None
        
        logger.debug(f"Finished trace: {trace_id} in {trace.duration:.2f}s")
        return trace
    
    def start_span(
        self,
        span_type: SpanType,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> Optional[str]:
        """Start a new span
        
        Args:
            span_type: Type of span
            name: Span name
            metadata: Optional metadata
            trace_id: Optional trace ID (defaults to current)
            
        Returns:
            Span ID or None if tracing disabled
        """
        if not self.enabled:
            return None
        
        trace_id = trace_id or self.current_trace_id
        if not trace_id or trace_id not in self.active_traces:
            logger.warning(f"No active trace found for span: {name}")
            return None
        
        span_id = f"span_{uuid.uuid4().hex[:12]}"
        parent_id = self.current_span_stack[-1] if self.current_span_stack else None
        
        span = SpanData(
            span_id=span_id,
            span_type=span_type,
            name=name,
            started_at=time.time(),
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.active_traces[trace_id].add_span(span)
        self.current_span_stack.append(span_id)
        
        logger.debug(f"Started span: {span_id} ({span_type.value}) - {name}")
        return span_id
    
    def finish_span(
        self,
        span_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Finish a span
        
        Args:
            span_id: Span ID to finish (defaults to current)
            error: Optional error message
            metadata: Additional metadata to add
        """
        if not self.enabled:
            return
        
        # Use current span if none specified
        if span_id is None:
            span_id = self.current_span_stack[-1] if self.current_span_stack else None
        
        if not span_id:
            logger.warning("No span to finish")
            return
        
        # Find the span in active traces
        for trace in self.active_traces.values():
            for span in trace.spans:
                if span.span_id == span_id:
                    span.ended_at = time.time()
                    if error:
                        span.error = error
                    if metadata:
                        span.metadata.update(metadata)
                    
                    # Remove from stack
                    if span_id in self.current_span_stack:
                        self.current_span_stack.remove(span_id)
                    
                    logger.debug(f"Finished span: {span_id} in {span.duration:.3f}s")
                    return
        
        logger.warning(f"Span not found: {span_id}")
    
    @contextmanager
    def trace(self, workflow_name: str, **metadata):
        """Context manager for tracing a workflow
        
        Args:
            workflow_name: Name of the workflow
            **metadata: Optional metadata
        """
        trace_id = self.create_trace(workflow_name)
        
        if metadata:
            self.add_trace_metadata(metadata, trace_id)
        
        try:
            yield trace_id
        except Exception as e:
            self.add_trace_metadata({"error": str(e)}, trace_id)
            raise
        finally:
            self.finish_trace(trace_id)
    
    @contextmanager
    def span(self, span_type: SpanType, name: str, **metadata):
        """Context manager for creating a span
        
        Args:
            span_type: Type of span
            name: Span name
            **metadata: Optional metadata
        """
        span_id = self.start_span(span_type, name, metadata)
        
        try:
            yield span_id
        except Exception as e:
            self.finish_span(span_id, error=str(e))
            raise
        else:
            self.finish_span(span_id)
    
    def add_trace_metadata(self, metadata: Dict[str, Any], trace_id: Optional[str] = None):
        """Add metadata to a trace"""
        if not self.enabled:
            return
        
        trace_id = trace_id or self.current_trace_id
        if trace_id in self.active_traces:
            self.active_traces[trace_id].metadata.update(metadata)
    
    def get_trace(self, trace_id: str) -> Optional[AgentTrace]:
        """Get a trace by ID"""
        # Check active traces
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]
        
        # Check completed traces
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
        
        return None
    
    def get_all_traces(self) -> List[AgentTrace]:
        """Get all traces (active and completed)"""
        return list(self.active_traces.values()) + self.completed_traces
    
    def clear_traces(self):
        """Clear all traces"""
        self.active_traces.clear()
        self.completed_traces.clear()
        self.current_trace_id = None
        self.current_span_stack.clear()
    
    def export_traces(self, format: str = "json") -> Union[List[Dict], str]:
        """Export traces in specified format
        
        Args:
            format: Export format ("json", "summary")
            
        Returns:
            Exported data
        """
        all_traces = self.get_all_traces()
        
        if format == "json":
            return [trace.to_dict() for trace in all_traces]
        
        elif format == "summary":
            summary = []
            for trace in all_traces:
                perf = trace.get_agent_performance()
                summary.append(
                    f"Trace: {trace.workflow_name} ({trace.trace_id})\n"
                    f"  Duration: {trace.duration:.2f}s\n"
                    f"  Agents: {perf['total_agents']}\n"
                    f"  Generations: {perf['total_generations']}\n"
                    f"  Errors: {perf['errors']}\n"
                )
            return "\n".join(summary)
        
        else:
            raise ValueError(f"Unknown format: {format}")


# Global trace manager instance
trace_manager = TraceManager()