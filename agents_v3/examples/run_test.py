#!/usr/bin/env python3
"""
Simple test runner for agents_v3 parallel orchestrator
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
from test_config import *


async def main():
    """Run test with single category"""
    
    print(f"🚀 Testing Parallel Orchestrator")
    print(f"📁 Category: {TEST_CATEGORY}")
    print(f"📊 Max stories: {MAX_STORIES_PER_CATEGORY or 'All'}")
    print(f"⚡ Concurrent: {MAX_CONCURRENT_STORIES}")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: API keys required")
        print("Set ANTHROPIC_API_KEY and GEMINI_API_KEY environment variables")
        return
    
    try:
        # Initialize orchestrator
        orchestrator = ParallelCategoryOrchestrator()
        
        # Configure for single category
        orchestrator.categories = {
            TEST_CATEGORY: orchestrator.categories[TEST_CATEGORY]
        }
        orchestrator.max_concurrent_stories = MAX_CONCURRENT_STORIES
        
        print("\n1️⃣ Initializing agents...")
        await orchestrator.initialize_agents()
        
        print("\n2️⃣ Discovering stories...")
        date = datetime.now().strftime("%Y-%m-%d")
        stories = await orchestrator.discover_all_categories(date)
        
        if not stories:
            print("❌ No stories discovered")
            return
        
        # Limit stories if configured
        if MAX_STORIES_PER_CATEGORY:
            orchestrator.discovered_stories = stories[:MAX_STORIES_PER_CATEGORY]
            print(f"   Limited to {MAX_STORIES_PER_CATEGORY} stories")
        
        print(f"\n3️⃣ Processing {len(orchestrator.discovered_stories)} stories...")
        start_time = datetime.now()
        results = await orchestrator.process_all_stories()
        duration = (datetime.now() - start_time).total_seconds()
        
        # Summary
        successful = sum(1 for r in results.values() if not r.get("errors"))
        citations = sum(len(r.get("citations", [])) for r in results.values())
        
        print(f"\n✅ Complete!")
        print(f"   • Duration: {duration:.1f}s ({duration/len(results):.1f}s per story)")
        print(f"   • Success: {successful}/{len(results)}")
        print(f"   • Citations: {citations} total")
        
        # Show performance report
        orchestrator.perf_logger.print_performance_report()
        
        # Save results
        if SAVE_RESULTS:
            filename = f"results_{TEST_CATEGORY}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        
        # Show sample
        if results:
            story_id = list(results.keys())[0]
            result = results[story_id]
            print(f"\n📰 Sample: {result['story']['headline_greek'][:60]}...")
            if result.get('synthesis'):
                print(f"\nSynthesis preview:")
                print("-" * 60)
                print(result['synthesis'][:300] + "...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'orchestrator' in locals():
            await orchestrator.message_bus.stop()


if __name__ == "__main__":
    asyncio.run(main())