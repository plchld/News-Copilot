#!/usr/bin/env python3
"""
Test the new parallel orchestrator with per-story agents
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator


async def test_parallel_orchestrator():
    """Test the parallel orchestrator with a small set of stories"""
    
    print("🧪 Testing Parallel Category Orchestrator")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set - using mock mode")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not set - using mock mode")
    
    try:
        # Initialize orchestrator
        orchestrator = ParallelCategoryOrchestrator()
        
        # Set small batch size for testing
        orchestrator.max_concurrent_stories = 2  # Process 2 stories at a time
        
        print("\n1️⃣ Initializing agents...")
        await orchestrator.initialize_agents()
        
        print("\n2️⃣ Discovering stories...")
        # For testing, we'll use today's date
        date = datetime.now().strftime("%Y-%m-%d")
        stories = await orchestrator.discover_all_categories(date)
        
        if not stories:
            print("❌ No stories discovered. Check API keys and network connection.")
            return
        
        # For testing, limit to first 2 stories per category (12 total)
        test_stories = []
        stories_by_category = {}
        for story in stories:
            if story.category not in stories_by_category:
                stories_by_category[story.category] = []
            if len(stories_by_category[story.category]) < 2:
                stories_by_category[story.category].append(story)
                test_stories.append(story)
        
        orchestrator.discovered_stories = test_stories
        print(f"\n📊 Limited to {len(test_stories)} stories for testing")
        
        print("\n3️⃣ Processing stories with parallel agents...")
        results = await orchestrator.process_all_stories()
        
        print("\n4️⃣ Results Summary:")
        print(f"  • Stories processed: {len(results)}")
        
        # Count successful vs failed
        successful = sum(1 for r in results.values() if not r.get("errors"))
        failed = len(results) - successful
        print(f"  • Successful: {successful}")
        print(f"  • Failed: {failed}")
        
        # Count citations
        total_citations = sum(len(r.get("citations", [])) for r in results.values())
        print(f"  • Total citations collected: {total_citations}")
        
        # Show sample result
        if results:
            first_key = list(results.keys())[0]
            first_result = results[first_key]
            print(f"\n5️⃣ Sample Result ({first_key}):")
            print(f"  • Story: {first_result['story']['headline_greek'][:60]}...")
            print(f"  • Context agents used: {list(first_result.get('context', {}).keys())}")
            print(f"  • Citations found: {len(first_result.get('citations', []))}")
            print(f"  • Fact-checks: {'✓' if first_result.get('factchecks') else '✗'}")
            print(f"  • Synthesis: {'✓' if first_result.get('synthesis') else '✗'}")
            
            if first_result.get('errors'):
                print(f"  • Errors: {first_result['errors']}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_minimal():
    """Minimal test with mock data to verify architecture"""
    
    print("\n🧪 Running minimal architecture test...")
    
    from agents_v3.utils.discovery_parser import ParsedStory
    
    # Create mock stories
    mock_stories = [
        ParsedStory(
            id=1,
            headline="Test Story 1",
            headline_greek="Δοκιμαστική Ιστορία 1",
            summary="This is a test story about Greek politics",
            source_name="Test Source",
            source_url="https://example.com/1",
            published_date="2024-01-30",
            stakeholders=["Test Party", "Government"],
            international_relevance_score=8,
            relevance_reasoning="High EU impact",
            category="Greek Political News"
        ),
        ParsedStory(
            id=2,
            headline="Test Story 2",
            headline_greek="Δοκιμαστική Ιστορία 2",
            summary="This is a test story about technology",
            source_name="Tech Source",
            source_url="https://example.com/2",
            published_date="2024-01-30",
            stakeholders=["Tech Company", "EU"],
            international_relevance_score=10,
            relevance_reasoning="Global tech impact",
            category="Technology News"
        )
    ]
    
    try:
        orchestrator = ParallelCategoryOrchestrator()
        orchestrator.discovered_stories = mock_stories
        
        print("✓ Orchestrator created")
        print(f"✓ Mock stories: {len(mock_stories)}")
        
        # Test agent factory
        from agents_v3.orchestration.parallel_category_orchestrator import AgentFactory
        
        test_agent = AgentFactory.create_context_agent("test_1", "greek")
        print(f"✓ Agent factory works: {test_agent.config.name}")
        
        # Test story processor
        from agents_v3.orchestration.parallel_category_orchestrator import StoryProcessor
        from agents_v3.communication import message_bus
        
        processor = StoryProcessor(mock_stories[0], message_bus)
        print(f"✓ Story processor created: {processor.story_id}")
        
        print("\n✅ Architecture test passed!")
        
    except Exception as e:
        print(f"\n❌ Architecture test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    
    print("🚀 Parallel Orchestrator Test Suite")
    print("=" * 60)
    
    # Run minimal test first
    asyncio.run(test_minimal())
    
    # Ask user if they want to run full test
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("GEMINI_API_KEY"):
        response = input("\n🤔 Run full test with API calls? (y/n): ")
        if response.lower() == 'y':
            asyncio.run(test_parallel_orchestrator())
    else:
        print("\n⚠️  Skipping full test - API keys not set")
        print("Set ANTHROPIC_API_KEY and GEMINI_API_KEY to run full test")


if __name__ == "__main__":
    main()