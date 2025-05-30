#!/usr/bin/env python3
"""Test with just one category to verify citation propagation"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator as CategoryOrchestrator


async def test_one_category():
    """Test pipeline with single category"""
    
    print("🧪 Testing with ONE Category")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: Please set ANTHROPIC_API_KEY and GEMINI_API_KEY environment variables")
        return
    
    # Initialize orchestrator
    orchestrator = CategoryOrchestrator()
    
    try:
        # Initialize agents
        print("1️⃣ Initializing agents...")
        await orchestrator.initialize_agents()
        
        # Use only Greek Political category for testing
        print("2️⃣ Using only Greek Political category...")
        test_categories = {
            "greek_political": orchestrator.categories["greek_political"]
        }
        orchestrator.categories = test_categories
        
        # Run the analysis
        print("3️⃣ Running analysis...")
        results = await orchestrator.run_daily_analysis("today")
        
        # Check results
        print("\n📊 Results Summary:")
        print(f"  • Stories discovered: {results['total_stories']}")
        print(f"  • Stories processed: {results['summary']['stories_processed']}")
        print(f"  • Duration: {results['summary']['duration_minutes']} minutes")
        
        # Check first story for citations
        if results['results']:
            first_story_id = list(results['results'].keys())[0]
            first_result = results['results'][first_story_id]
            
            print(f"\n📰 First Story Analysis:")
            print(f"  • Headline: {first_result['story']['headline_greek']}")
            print(f"  • Citations collected: {len(first_result.get('citations', []))}")
            
            if first_result.get('citations'):
                print("\n  Citation sources:")
                agent_counts = {}
                for citation in first_result['citations']:
                    agent = citation.get('source_agent', 'unknown')
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
                for agent, count in agent_counts.items():
                    print(f"    - {agent}: {count} citations")
            
            # Check synthesis
            synthesis = first_result.get('synthesis', '')
            if synthesis:
                # Count citation references
                ref_count = sum(1 for i in range(1, 50) if f'[{i}]' in synthesis)
                print(f"\n  Synthesis includes {ref_count} citation references")
                
                # Check for source section
                if 'Πηγές Αναφοράς' in synthesis:
                    print("  ✅ Synthesis includes full source list")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            await orchestrator.message_bus.stop()
        except:
            pass


if __name__ == "__main__":
    print("\nSingle Category Test")
    print("Testing Greek Political category only")
    print("Low search threshold (0.3) should trigger many searches\n")
    
    asyncio.run(test_one_category())