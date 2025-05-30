#!/usr/bin/env python3
"""Test citation propagation from Gemini agents to Anthropic synthesis"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator as CategoryOrchestrator


async def test_citation_propagation():
    """Test that citations from Gemini agents are propagated to synthesis"""
    
    print("🔬 Testing Citation Propagation Pipeline")
    print("=" * 60)
    print("Objective: Verify citations from Gemini agents reach synthesis")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: Please set ANTHROPIC_API_KEY and GEMINI_API_KEY environment variables")
        return
    
    # Initialize orchestrator
    orchestrator = CategoryOrchestrator()
    
    try:
        # Initialize agents
        print("\n1️⃣ Initializing agents...")
        await orchestrator.initialize_agents()
        
        # Configure for quick test - only one category
        print("\n2️⃣ Limiting to one category for quick test...")
        test_categories = {
            "greek_political": orchestrator.categories["greek_political"]
        }
        orchestrator.categories = test_categories
        
        # Discover stories
        print("\n3️⃣ Discovering stories (expecting citations from Gemini search)...")
        stories = await orchestrator.discover_all_categories("today")
        
        if not stories:
            print("❌ No stories discovered!")
            return
        
        # Process just the first story
        print(f"\n4️⃣ Processing first story: {stories[0].headline_greek}")
        print(f"   International relevance: {stories[0].international_relevance_score}/10")
        
        # Process the story
        result = await orchestrator._process_single_story(stories[0])
        
        # Check results
        print("\n5️⃣ Checking citation propagation:")
        
        citations = result.get("citations", [])
        if citations:
            print(f"   ✅ Found {len(citations)} total citations collected from agents:")
            for i, citation in enumerate(citations[:5], 1):
                print(f"      {i}. {citation.get('title', 'No title')} - {citation.get('url', '')[:50]}...")
        else:
            print("   ❌ No citations found (agents may not have triggered searches)")
        
        # Check synthesis
        synthesis = result.get("synthesis", "")
        if synthesis:
            print("\n6️⃣ Synthesis content preview:")
            print("   " + synthesis[:200] + "...")
            
            # Check if synthesis contains citation references
            has_citation_refs = any(f"[{i}]" in synthesis for i in range(1, 11))
            if has_citation_refs:
                print("   ✅ Synthesis contains citation references [1], [2], etc.")
            else:
                print("   ⚠️ Synthesis doesn't contain citation references (may not have citations)")
            
            # Check if synthesis contains source section
            if "Πηγές Αναφοράς" in synthesis or "Sources" in synthesis:
                print("   ✅ Synthesis includes sources section")
        
        # Print errors if any
        if result.get("errors"):
            print(f"\n⚠️ Errors encountered: {result['errors']}")
        
        # Cleanup
        await orchestrator.message_bus.stop()
        
        print("\n✅ Citation propagation test completed!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to cleanup
        try:
            await orchestrator.message_bus.stop()
        except:
            pass


if __name__ == "__main__":
    print("\nCitation Propagation Test")
    print("This test verifies that citations from Gemini agents (discovery, context, fact-check)")
    print("are properly collected and passed to the Anthropic synthesis agent.")
    print("\nNote: Citations only appear when Gemini agents trigger searches.")
    print("With search_threshold=0.3, most queries should trigger searches.\n")
    
    asyncio.run(test_citation_propagation())