"""Basic usage examples for News Copilot Agents v2"""

import asyncio
import os
from datetime import datetime

from ..orchestrator import NewsIntelligenceOrchestrator, OrchestrationConfig
from ..agents.discovery import DiscoveryAgent, DISCOVERY_CATEGORIES
from ..agents.perspectives import GreekPerspectiveAgent
from ..tracing import trace_manager, TraceVisualizer


async def example_single_discovery():
    """Example: Run a single discovery agent"""
    print("🔍 Example: Single Discovery Agent")
    print("-" * 30)
    
    # Create a discovery agent for Greek politics
    category_config = DISCOVERY_CATEGORIES["greek_politics"]
    agent = DiscoveryAgent(category_config, provider="grok")
    
    # Discover today's stories
    result = await agent.discover(time_range="today")
    
    print(f"Category: {result.category}")
    print(f"Stories found: {len(result.stories)}")
    
    for i, story in enumerate(result.stories, 1):
        print(f"\n{i}. {story.headline}")
        print(f"   Relevance: {story.greek_relevance:.1f}")
        print(f"   Sources: {story.initial_sources_found}")
        print(f"   Why important: {story.why_important}")


async def example_perspective_analysis():
    """Example: Analyze a topic from Greek perspective"""
    print("\n🇬🇷 Example: Greek Perspective Analysis")
    print("-" * 35)
    
    # Create Greek perspective agent
    agent = GreekPerspectiveAgent(provider="grok")
    
    # Analyze a sample topic
    topic = "EU AI Regulations impact on Greek tech sector"
    result = await agent.analyze(topic)
    
    print(f"Topic: {result.topic}")
    print(f"Summary: {result.summary}")
    print(f"\nDominant narrative: {result.analysis.dominant_narrative}")
    print(f"Unique angles: {', '.join(result.analysis.unique_angles)}")
    print(f"Source diversity: {result.analysis.source_diversity}")
    print(f"Confidence: {result.confidence:.1f}")


async def example_full_orchestration():
    """Example: Complete news intelligence workflow"""
    print("\n🎼 Example: Full Intelligence Orchestration")
    print("-" * 40)
    
    # Configure the orchestration
    config = OrchestrationConfig(
        categories_to_scan=["greek_politics", "global_politics", "economy_business"],
        max_stories_per_category=3,
        max_stories_to_analyze=5,
        discovery_provider="grok",
        synthesis_provider="anthropic",
        include_timeline=True,
        include_jargon=True,
        include_social_pulse=True
    )
    
    # Create orchestrator
    orchestrator = NewsIntelligenceOrchestrator(config)
    
    # Generate daily intelligence with tracing
    with trace_manager.trace("Daily Intelligence Example") as trace_id:
        print("🚀 Generating daily intelligence report...")
        
        report = await orchestrator.generate_daily_intelligence(
            focus_topics=["artificial intelligence", "economy"],
            priority_categories=["greek_politics"]
        )
        
        print(f"✅ Report generated!")
        print(f"Processing time: {report['processing_time_seconds']:.1f}s")
        print(f"Stories analyzed: {len(report['stories'])}")
        
        # Show summary
        summary = report['summary']
        print(f"\n📊 Summary:")
        print(f"Total stories: {summary['total_stories']}")
        print(f"Categories: {', '.join(summary['by_category'].keys())}")
        print(f"Priority distribution: {summary['priority_distribution']}")
        
        # Show top stories
        print(f"\n📰 Top Stories:")
        for story in summary['top_stories']:
            print(f"- [{story['priority'].upper()}] {story['headline']}")
        
        # Show first story details if available
        if report['stories']:
            first_story = report['stories'][0]
            print(f"\n🔍 First Story Details:")
            print(f"ID: {first_story['id']}")
            print(f"Category: {first_story['category']}")
            print(f"Greek relevance: {first_story['greek_relevance']:.1f}")
            print(f"Completeness: {first_story['metadata']['completeness_score']:.1f}")
            
            if first_story.get('narrative'):
                narrative = first_story['narrative']['narrative']
                print(f"\nNarrative intro: {narrative['introduction'][:100]}...")
                
                if narrative.get('agreements'):
                    print(f"Key agreements: {', '.join(narrative['agreements'][:2])}")
    
    # Show tracing results
    trace = trace_manager.get_trace(trace_id)
    if trace:
        print(f"\n📈 Execution Trace:")
        TraceVisualizer.print_trace_tree(trace)


async def example_custom_agent():
    """Example: Create and use a custom agent"""
    print("\n🔧 Example: Custom Agent")
    print("-" * 20)
    
    from ..providers import MultiProviderAgent
    from ..tools import search_web_tool
    
    # Create a custom financial analysis agent
    agent = MultiProviderAgent(
        name="greek_finance_analyzer",
        instructions="""You are a financial analyst specializing in Greek markets.
        
        Analyze Greek financial news and provide insights on:
        - Market impact on major Greek companies
        - Currency effects (EUR/USD) 
        - Tourism sector implications
        - Government fiscal policy effects
        
        Always provide specific recommendations for Greek investors.""",
        provider="grok",  # Or "anthropic" or "gemini"
        tools=[search_web_tool],
        temperature=0.3  # Lower temperature for analytical tasks
    )
    
    # Use the custom agent
    topic = "Greek banking sector Q4 2024 results"
    response = await agent.run(f"Analyze: {topic}")
    
    print(f"Analysis from {response.provider}:")
    print(f"Model: {response.model}")
    print(f"Content: {response.content[:300]}...")
    if response.usage:
        print(f"Tokens used: {response.usage.get('total_tokens', 'N/A')}")


async def example_provider_comparison():
    """Example: Compare responses from different providers"""
    print("\n⚖️ Example: Provider Comparison")
    print("-" * 30)
    
    from ..providers import MultiProviderAgent
    
    # Create same agent with different providers
    prompt = "Summarize the current state of AI regulation in the EU in exactly 100 words"
    
    providers = ["grok", "anthropic", "gemini"]
    responses = {}
    
    for provider in providers:
        try:
            agent = MultiProviderAgent(
                name=f"summarizer_{provider}",
                instructions="You are a concise policy analyst.",
                provider=provider,
                temperature=0.5
            )
            
            response = await agent.run(prompt)
            responses[provider] = {
                "content": response.content,
                "model": response.model,
                "usage": response.usage
            }
            print(f"✅ {provider}: {response.model}")
            
        except Exception as e:
            print(f"❌ {provider}: Error - {e}")
            responses[provider] = {"error": str(e)}
    
    # Compare responses
    print(f"\n📝 Response Comparison:")
    for provider, data in responses.items():
        if "error" not in data:
            word_count = len(data["content"].split())
            print(f"\n{provider.upper()} ({data['model']}):")
            print(f"Word count: {word_count}")
            print(f"Preview: {data['content'][:150]}...")
        else:
            print(f"\n{provider.upper()}: {data['error']}")


async def example_performance_monitoring():
    """Example: Monitor performance with tracing"""
    print("\n📊 Example: Performance Monitoring")
    print("-" * 32)
    
    from ..agents.synthesis import NarrativeSynthesisAgent
    
    # Clear existing traces
    trace_manager.clear_traces()
    
    # Run multiple operations to collect performance data
    agent = NarrativeSynthesisAgent(provider="anthropic")
    
    test_cases = [
        ("Simple news", {"greek": "Simple Greek view", "international": "Simple intl view"}),
        ("Complex politics", {"greek": "Complex Greek political analysis", 
                             "international": "Complex international view",
                             "opposing": "Alternative perspectives"}),
        ("Technical topic", {"greek": "Technical Greek analysis with jargon",
                            "international": "Technical international view",
                            "facts": "Verified technical facts"})
    ]
    
    for i, (topic, perspectives) in enumerate(test_cases, 1):
        with trace_manager.trace(f"Synthesis Test {i}"):
            result = await agent.synthesize(topic, perspectives)
            print(f"✅ Test {i}: {topic} - Completeness: {result.completeness_score:.1f}")
    
    # Analyze performance
    all_traces = trace_manager.get_all_traces()
    print(f"\n📈 Performance Analysis:")
    TraceVisualizer.print_performance_report(all_traces)
    
    # Export traces for further analysis
    json_export = trace_manager.export_traces("json")
    print(f"Exported {len(json_export)} traces to JSON format")


async def main():
    """Run all examples"""
    print("🧪 News Copilot Agents v2 - Usage Examples")
    print("=" * 50)
    
    # Check if API keys are available
    required_keys = ["XAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    available_keys = {key: bool(os.getenv(key)) for key in required_keys}
    
    print("🔑 API Keys Status:")
    for key, available in available_keys.items():
        status = "✅" if available else "❌"
        print(f"   {key}: {status}")
    
    if not any(available_keys.values()):
        print("\n⚠️  No API keys found. Examples will use mock responses.")
        print("   Set environment variables to test with real APIs:")
        for key in required_keys:
            print(f"   export {key}=your_key_here")
    
    print("\n" + "=" * 50)
    
    try:
        # Run examples
        await example_single_discovery()
        await example_perspective_analysis()
        await example_full_orchestration()
        await example_custom_agent()
        await example_provider_comparison()
        await example_performance_monitoring()
        
        print("\n🎉 All examples completed successfully!")
        
        print("\n💡 Key Takeaways:")
        print("   ✓ Multi-provider support (Grok, Anthropic, Gemini)")
        print("   ✓ Modular agent architecture")
        print("   ✓ Comprehensive tracing and debugging")
        print("   ✓ Greek news intelligence specialization")
        print("   ✓ Performance monitoring and optimization")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())