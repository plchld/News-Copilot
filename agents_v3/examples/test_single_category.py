#!/usr/bin/env python3
"""
Test the parallel orchestrator with a single category
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator


# Configuration
SINGLE_CATEGORY = "technology"  # Options: greek_political, greek_economic, international_political, international_economic, science, technology
MAX_STORIES = 3  # Limit number of stories to process (None for all 10)


async def test_single_category():
    """Test with a single news category"""
    
    print(f"🧪 Testing Single Category: {SINGLE_CATEGORY}")
    print(f"📐 Architecture: Parallel (per-story agents)")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: Both ANTHROPIC_API_KEY and GEMINI_API_KEY must be set")
        print("Export your API keys:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export GEMINI_API_KEY='your-key'")
        return
    
    try:
        # Initialize parallel orchestrator
        orchestrator = ParallelCategoryOrchestrator()
        orchestrator.max_concurrent_stories = 2  # Process 2 at a time for testing
        
        # Limit to single category
        original_categories = orchestrator.categories
        orchestrator.categories = {
            SINGLE_CATEGORY: original_categories[SINGLE_CATEGORY]
        }
        
        print(f"\n1️⃣ Initializing agents for {orchestrator.categories[SINGLE_CATEGORY]['name']}...")
        await orchestrator.initialize_agents()
        
        print("\n2️⃣ Discovering stories...")
        date = datetime.now().strftime("%Y-%m-%d")
        stories = await orchestrator.discover_all_categories(date)
        
        if not stories:
            print("❌ No stories discovered. Check network connection.")
            return
        
        # Limit stories if requested
        if MAX_STORIES and len(stories) > MAX_STORIES:
            orchestrator.discovered_stories = stories[:MAX_STORIES]
            print(f"\n📊 Limited to {MAX_STORIES} stories for testing")
        
        print(f"\n3️⃣ Processing {len(orchestrator.discovered_stories)} stories...")
        start_time = datetime.now()
        results = await orchestrator.process_all_stories()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Processing completed in {duration:.1f} seconds")
        
        # Analyze results
        print("\n4️⃣ Results Analysis:")
        print(f"  • Stories processed: {len(results)}")
        
        successful = 0
        total_citations = 0
        
        for story_id, result in results.items():
            if not result.get("errors"):
                successful += 1
            citations = result.get("citations", [])
            total_citations += len(citations)
            
            # Print story summary
            story = result["story"]
            print(f"\n  📰 {story['headline_greek'][:60]}...")
            print(f"     - Relevance score: {story['international_relevance_score']}/10")
            print(f"     - Contexts used: {list(result.get('context', {}).keys())}")
            print(f"     - Citations: {len(citations)}")
            
            # Show fact-check summary
            if result.get("factchecks", {}).get("verified_claims"):
                claims = result["factchecks"]["verified_claims"]
                print(f"     - Claims verified: {len(claims)}")
            
            # Show errors if any
            if result.get("errors"):
                print(f"     - ❌ Errors: {result['errors']}")
        
        print(f"\n📊 Summary:")
        print(f"  • Success rate: {successful}/{len(results)} ({(successful/len(results)*100):.1f}%)")
        print(f"  • Total citations: {total_citations}")
        print(f"  • Avg citations/story: {total_citations/len(results):.1f}")
        print(f"  • Processing speed: {duration/len(results):.1f} sec/story")
        
        # Save detailed results
        output_file = f"test_results_{SINGLE_CATEGORY}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "category": SINGLE_CATEGORY,
                "architecture": "parallel",
                "stories_processed": len(results),
                "duration_seconds": duration,
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Show sample synthesis
        if successful > 0:
            for story_id, result in results.items():
                if result.get("synthesis"):
                    print(f"\n5️⃣ Sample Synthesis ({story_id}):")
                    print("-" * 60)
                    print(result["synthesis"][:500] + "...")
                    break
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if hasattr(orchestrator, 'message_bus'):
            await orchestrator.message_bus.stop()


async def test_performance():
    """Test performance with different batch sizes"""
    
    print("⚡ Performance Test with Different Batch Sizes")
    print("=" * 60)
    
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: API keys required")
        return
    
    try:
        # First discover stories
        print("\n1️⃣ Discovering stories...")
        orchestrator = ParallelCategoryOrchestrator()
        orchestrator.categories = {
            SINGLE_CATEGORY: orchestrator.categories[SINGLE_CATEGORY]
        }
        await orchestrator.initialize_agents()
        
        date = datetime.now().strftime("%Y-%m-%d")
        stories = await orchestrator.discover_all_categories(date)
        
        if not stories:
            print("❌ No stories discovered")
            return
        
        # Test with 6 stories
        test_stories = stories[:6]
        print(f"\n📊 Using {len(test_stories)} stories for performance test")
        
        # Test different batch sizes
        batch_sizes = [1, 2, 3, 6]
        results = {}
        
        for batch_size in batch_sizes:
            print(f"\n🔄 Testing batch size: {batch_size}")
            orch = ParallelCategoryOrchestrator()
            orch.categories = {SINGLE_CATEGORY: orch.categories[SINGLE_CATEGORY]}
            orch.discovered_stories = test_stories
            orch.max_concurrent_stories = batch_size
            
            await orch.initialize_agents()
            
            start = datetime.now()
            batch_results = await orch.process_all_stories()
            duration = (datetime.now() - start).total_seconds()
            
            await orch.message_bus.stop()
            
            results[batch_size] = {
                'duration': duration,
                'citations': sum(len(r.get("citations", [])) for r in batch_results.values())
            }
            
            print(f"  • Duration: {duration:.1f}s ({duration/len(test_stories):.1f}s per story)")
            print(f"  • Citations: {results[batch_size]['citations']}")
        
        # Show summary
        print("\n📊 Performance Summary:")
        print("Batch Size | Duration | Speed/Story | Citations")
        print("-" * 50)
        for batch_size, data in results.items():
            print(f"{batch_size:^10} | {data['duration']:>8.1f}s | {data['duration']/len(test_stories):>10.1f}s | {data['citations']:^9}")
        
        # Find optimal batch size
        optimal = min(results.items(), key=lambda x: x[1]['duration'])
        print(f"\n✨ Optimal batch size: {optimal[0]} (completed in {optimal[1]['duration']:.1f}s)")
        
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    
    print("🚀 Single Category Test Suite")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  • Category: {SINGLE_CATEGORY}")
    print(f"  • Architecture: {'Parallel' if USE_PARALLEL else 'Sequential'}")
    print(f"  • Max stories: {MAX_STORIES or 'All'}")
    
    choice = input("\nSelect test:\n1. Test single category\n2. Performance test (batch sizes)\n> ")
    
    if choice == "2":
        asyncio.run(test_performance())
    else:
        asyncio.run(test_single_category())


if __name__ == "__main__":
    main()