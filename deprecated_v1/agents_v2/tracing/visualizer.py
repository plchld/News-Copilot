"""Trace visualization utilities"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .trace_manager import AgentTrace, SpanData, SpanType


class TraceVisualizer:
    """Utilities for visualizing traces"""
    
    @staticmethod
    def print_trace_tree(trace: AgentTrace, show_metadata: bool = False):
        """Print a tree view of the trace"""
        print(f"\n📊 Trace: {trace.workflow_name} ({trace.trace_id})")
        print(f"Duration: {trace.duration:.2f}s")
        print(f"Spans: {len(trace.spans)}")
        
        if trace.metadata:
            print(f"Metadata: {trace.metadata}")
        
        # Build tree structure
        root_spans = [s for s in trace.spans if s.parent_id is None]
        children_map = {}
        
        for span in trace.spans:
            if span.parent_id:
                if span.parent_id not in children_map:
                    children_map[span.parent_id] = []
                children_map[span.parent_id].append(span)
        
        # Print tree
        def print_span(span: SpanData, indent: int = 0):
            prefix = "  " * indent + ("├─ " if indent > 0 else "")
            icon = TraceVisualizer._get_span_icon(span.span_type)
            status = "❌" if span.error else "✅"
            
            duration_str = f"{span.duration:.3f}s" if span.duration else "running"
            
            print(f"{prefix}{icon} {span.name} ({span.span_type.value}) - {duration_str} {status}")
            
            if span.error:
                print(f"{'  ' * (indent + 1)}Error: {span.error}")
            
            if show_metadata and span.metadata:
                for key, value in span.metadata.items():
                    print(f"{'  ' * (indent + 1)}{key}: {value}")
            
            # Print children
            children = children_map.get(span.span_id, [])
            for child in children:
                print_span(child, indent + 1)
        
        for root_span in root_spans:
            print_span(root_span)
        
        print()
    
    @staticmethod
    def _get_span_icon(span_type: SpanType) -> str:
        """Get icon for span type"""
        icons = {
            SpanType.AGENT: "🤖",
            SpanType.GENERATION: "💭",
            SpanType.FUNCTION_CALL: "🔧",
            SpanType.SEARCH: "🔍",
            SpanType.SYNTHESIS: "🔗",
            SpanType.ERROR: "❌",
            SpanType.CUSTOM: "📝"
        }
        return icons.get(span_type, "📌")
    
    @staticmethod
    def generate_performance_report(traces: List[AgentTrace]) -> Dict[str, Any]:
        """Generate performance report from traces"""
        if not traces:
            return {"error": "No traces to analyze"}
        
        total_duration = sum(t.duration or 0 for t in traces)
        total_spans = sum(len(t.spans) for t in traces)
        
        # Agent performance
        agent_stats = {}
        generation_stats = {}
        error_count = 0
        
        for trace in traces:
            perf = trace.get_agent_performance()
            
            for agent in perf["agents_used"]:
                if agent not in agent_stats:
                    agent_stats[agent] = {"count": 0, "total_duration": 0}
                agent_stats[agent]["count"] += 1
            
            error_count += perf["errors"]
            
            # Generation stats
            for span in trace.get_spans_by_type(SpanType.GENERATION):
                model = span.metadata.get("model", "unknown")
                if model not in generation_stats:
                    generation_stats[model] = {"count": 0, "total_duration": 0, "total_tokens": 0}
                
                generation_stats[model]["count"] += 1
                if span.duration:
                    generation_stats[model]["total_duration"] += span.duration
                generation_stats[model]["total_tokens"] += span.metadata.get("tokens", 0)
        
        return {
            "summary": {
                "total_traces": len(traces),
                "total_duration": total_duration,
                "total_spans": total_spans,
                "error_count": error_count,
                "avg_trace_duration": total_duration / len(traces)
            },
            "agent_performance": agent_stats,
            "generation_performance": generation_stats,
            "slowest_traces": [
                {
                    "trace_id": t.trace_id,
                    "workflow": t.workflow_name,
                    "duration": t.duration
                }
                for t in sorted(traces, key=lambda x: x.duration or 0, reverse=True)[:5]
            ]
        }
    
    @staticmethod
    def print_performance_report(traces: List[AgentTrace]):
        """Print a formatted performance report"""
        report = TraceVisualizer.generate_performance_report(traces)
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return
        
        summary = report["summary"]
        print(f"\n📈 Performance Report")
        print(f"═══════════════════")
        print(f"Total traces: {summary['total_traces']}")
        print(f"Total duration: {summary['total_duration']:.2f}s")
        print(f"Average duration: {summary['avg_trace_duration']:.2f}s")
        print(f"Total spans: {summary['total_spans']}")
        print(f"Errors: {summary['error_count']}")
        
        # Agent performance
        if report["agent_performance"]:
            print(f"\n🤖 Agent Performance:")
            for agent, stats in report["agent_performance"].items():
                print(f"  {agent}: {stats['count']} runs")
        
        # Generation performance  
        if report["generation_performance"]:
            print(f"\n💭 Generation Performance:")
            for model, stats in report["generation_performance"].items():
                avg_duration = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
                avg_tokens = stats["total_tokens"] / stats["count"] if stats["count"] > 0 else 0
                print(f"  {model}:")
                print(f"    Calls: {stats['count']}")
                print(f"    Avg duration: {avg_duration:.3f}s")
                print(f"    Avg tokens: {avg_tokens:.0f}")
        
        # Slowest traces
        if report["slowest_traces"]:
            print(f"\n🐌 Slowest Traces:")
            for trace in report["slowest_traces"][:3]:
                print(f"  {trace['workflow']}: {trace['duration']:.2f}s ({trace['trace_id']})")
        
        print()
    
    @staticmethod
    def export_for_web(traces: List[AgentTrace]) -> str:
        """Export traces in format suitable for web visualization"""
        # Simple format that could be consumed by a web dashboard
        web_data = {
            "traces": [],
            "summary": TraceVisualizer.generate_performance_report(traces)
        }
        
        for trace in traces:
            trace_data = {
                "id": trace.trace_id,
                "name": trace.workflow_name,
                "start": trace.started_at,
                "end": trace.ended_at,
                "duration": trace.duration,
                "spans": []
            }
            
            for span in trace.spans:
                span_data = {
                    "id": span.span_id,
                    "type": span.span_type.value,
                    "name": span.name,
                    "start": span.started_at,
                    "end": span.ended_at,
                    "duration": span.duration,
                    "parent": span.parent_id,
                    "error": span.error,
                    "metadata": span.metadata
                }
                trace_data["spans"].append(span_data)
            
            web_data["traces"].append(trace_data)
        
        return json.dumps(web_data, indent=2)