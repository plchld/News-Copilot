"""Test agents with full tracing and visualization"""

import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Mock the openai module before importing our agents
sys.modules['openai'] = MagicMock()

from agents_v2.tracing import trace_manager, TraceVisualizer, SpanType
from agents_v2.orchestrator import NewsIntelligenceOrchestrator, OrchestrationConfig
from agents_v2.providers import MultiProviderAgent
from mock_responses import MockAgentResponses


async def test_full_workflow_with_tracing():
    """Test complete workflow with detailed tracing"""
    print("🔍 Testing News Intelligence with Full Tracing")
    print("=" * 50)
    
    # Clear any existing traces
    trace_manager.clear_traces()
    
    # Mock response class
    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MagicMock(message=MagicMock(content=content), finish_reason="stop")]
            self.usage = MagicMock(model_dump=lambda: {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50})
    
    # Create mock API function that returns appropriate responses
    async def mock_api_call(self, params):
        """Mock API call that simulates different agents"""
        agent_name = self.name
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        if "discovery" in agent_name:
            category = agent_name.replace("discovery_", "")
            return MockResponse(MockAgentResponses.discovery_response(category))
        elif agent_name == "greek_perspective":
            return MockResponse(MockAgentResponses.greek_perspective_response())
        elif agent_name == "international_perspective":
            return MockResponse(MockAgentResponses.international_perspective_response())
        elif agent_name == "opposing_view":
            return MockResponse(MockAgentResponses.opposing_view_response())
        elif agent_name == "fact_verification":
            return MockResponse(MockAgentResponses.fact_verification_response())
        elif agent_name == "narrative_synthesis":
            return MockResponse(MockAgentResponses.narrative_synthesis_response())
        elif agent_name == "jargon_context":
            return MockResponse(MockAgentResponses.jargon_response())
        elif agent_name == "timeline_builder":
            return MockResponse(MockAgentResponses.timeline_response())
        elif agent_name == "social_pulse":
            return MockResponse(MockAgentResponses.social_pulse_response())
        else:
            return MockResponse('{"error": "Unknown agent"}')
    
    # Set up configuration for faster testing
    config = OrchestrationConfig(
        categories_to_scan=["greek_politics", "global_politics"],
        max_stories_per_category=1,
        max_stories_to_analyze=2,
        include_timeline=True,
        include_jargon=True,
        include_social_pulse=True,
        agent_timeout_seconds=10
    )
    
    orchestrator = NewsIntelligenceOrchestrator(config)
    
    # Patch the API calls
    with patch.object(MultiProviderAgent, '_call_api', new=mock_api_call):
        
        # Run the complete workflow with tracing
        with trace_manager.trace("Daily News Intelligence") as trace_id:
            print(f"\n🚀 Starting workflow (trace: {trace_id})")
            
            # Add some workflow metadata
            trace_manager.add_trace_metadata({
                "categories": config.categories_to_scan,
                "max_stories": config.max_stories_to_analyze,
                "timestamp": "2025-01-30T10:00:00Z"
            })
            
            # Custom spans for workflow phases
            with trace_manager.span(SpanType.CUSTOM, "Phase 1: Discovery"):
                print("  🔍 Phase 1: Discovery...")
                await asyncio.sleep(0.05)  # Simulate discovery time
            
            # Generate the intelligence report
            with trace_manager.span(SpanType.CUSTOM, "Full Intelligence Generation"):
                report = await orchestrator.generate_daily_intelligence()
            
            print(f"  ✅ Workflow completed!")
            print(f"  📊 Stories processed: {len(report['stories'])}")
            print(f"  ⏱️  Processing time: {report['processing_time_seconds']:.2f}s")
    
    # Get the completed trace
    completed_trace = trace_manager.get_trace(trace_id)
    if completed_trace:
        print(f"\n📈 Trace Analysis:")
        print(f"   Total duration: {completed_trace.duration:.2f}s")
        print(f"   Total spans: {len(completed_trace.spans)}")
        
        # Show performance metrics
        perf = completed_trace.get_agent_performance()
        print(f"   Agents used: {perf['total_agents']}")
        print(f"   Generations: {perf['total_generations']}")
        print(f"   Errors: {perf['errors']}")
        print(f"   Agent types: {', '.join(perf['agents_used'])}")
        
        # Print detailed trace tree
        TraceVisualizer.print_trace_tree(completed_trace, show_metadata=True)
        
        # Print performance report
        TraceVisualizer.print_performance_report([completed_trace])
    
    print("\n✅ Tracing test completed successfully!")
    return report, completed_trace


async def test_error_handling_with_tracing():
    """Test error handling and how it appears in traces"""
    print("\n🚨 Testing Error Handling with Tracing")
    print("=" * 40)
    
    # Create an agent that will fail
    class FailingAgent(MultiProviderAgent):
        async def _call_api(self, params):
            raise Exception("Simulated API failure")
    
    agent = FailingAgent(
        name="failing_test_agent",
        instructions="This agent will fail",
        provider="grok"
    )
    
    # Test with tracing
    with trace_manager.trace("Error Test Workflow") as trace_id:
        try:
            with trace_manager.span(SpanType.AGENT, "Failing Agent Test"):
                await agent.run("Test message")
        except Exception as e:
            print(f"  ❌ Expected error caught: {e}")
    
    # Check the trace
    error_trace = trace_manager.get_trace(trace_id)
    if error_trace:
        print(f"\n📊 Error Trace Analysis:")
        TraceVisualizer.print_trace_tree(error_trace)
        
        # Count errors
        error_spans = [s for s in error_trace.spans if s.error]
        print(f"   Error spans: {len(error_spans)}")
        for span in error_spans:
            print(f"   - {span.name}: {span.error}")
    
    print("✅ Error handling test completed!")


async def test_concurrent_agents_tracing():
    """Test how tracing handles concurrent agent execution"""
    print("\n⚡ Testing Concurrent Agents with Tracing")
    print("=" * 40)
    
    # Mock response
    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MagicMock(message=MagicMock(content=content), finish_reason="stop")]
            self.usage = MagicMock(model_dump=lambda: {"total_tokens": 100})
    
    async def mock_concurrent_api(self, params):
        # Simulate variable processing time
        await asyncio.sleep(0.1 + (hash(self.name) % 100) / 1000)
        return MockResponse(f'{{"result": "Response from {self.name}"}}')
    
    # Create multiple agents
    agents = [
        MultiProviderAgent(f"agent_{i}", f"Instructions for agent {i}", "grok")
        for i in range(4)
    ]
    
    with patch.object(MultiProviderAgent, '_call_api', new=mock_concurrent_api):
        with trace_manager.trace("Concurrent Agents Test") as trace_id:
            
            # Run agents concurrently
            async def run_agent(agent):
                with trace_manager.span(SpanType.CUSTOM, f"Concurrent Group"):
                    return await agent.run(f"Test message for {agent.name}")
            
            # Execute all agents concurrently
            print("  🏃‍♂️ Running 4 agents concurrently...")
            results = await asyncio.gather(*[run_agent(agent) for agent in agents])
            print(f"  ✅ All {len(results)} agents completed")
    
    # Analyze concurrent trace
    concurrent_trace = trace_manager.get_trace(trace_id)
    if concurrent_trace:
        print(f"\n📊 Concurrent Execution Analysis:")
        TraceVisualizer.print_trace_tree(concurrent_trace)
        
        # Check span overlap
        agent_spans = concurrent_trace.get_spans_by_type(SpanType.AGENT)
        print(f"   Agent spans: {len(agent_spans)}")
        
        # Calculate concurrency
        if len(agent_spans) > 1:
            total_sequential = sum(s.duration or 0 for s in agent_spans)
            actual_duration = concurrent_trace.duration or 0
            concurrency_ratio = total_sequential / actual_duration if actual_duration > 0 else 1
            print(f"   Concurrency achieved: {concurrency_ratio:.1f}x speedup")
    
    print("✅ Concurrent agents test completed!")


async def main():
    """Run all tracing tests"""
    print("🧪 News Copilot Agents v2 - Advanced Tracing Tests")
    print("=" * 60)
    
    try:
        # Test 1: Full workflow
        report, main_trace = await test_full_workflow_with_tracing()
        
        # Test 2: Error handling
        await test_error_handling_with_tracing()
        
        # Test 3: Concurrent execution
        await test_concurrent_agents_tracing()
        
        # Final summary
        all_traces = trace_manager.get_all_traces()
        print(f"\n📋 Final Summary:")
        print(f"   Total traces collected: {len(all_traces)}")
        
        # Export traces for analysis
        json_export = trace_manager.export_traces("json")
        summary_export = trace_manager.export_traces("summary")
        
        print(f"\n📄 Trace Summary:")
        print(summary_export)
        
        # Web export example
        web_export = TraceVisualizer.export_for_web(all_traces)
        print(f"\n🌐 Web export generated ({len(web_export)} characters)")
        
        print("\n🎉 All tracing tests completed successfully!")
        print("\n💡 Tracing Benefits Demonstrated:")
        print("   ✓ Agent execution visibility")
        print("   ✓ Performance profiling")
        print("   ✓ Error tracking and debugging")
        print("   ✓ Concurrency analysis")
        print("   ✓ Workflow optimization insights")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())