#!/usr/bin/env python3
"""
Test the orchestrator with a single story for detailed debugging
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

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator, StoryProcessor
from agents_v3.utils.discovery_parser import ParsedStory
from agents_v3.communication import message_bus


async def test_single_story_detailed():
    """Test processing of a single story with detailed output"""
    
    print("🔍 Single Story Detailed Test")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: API keys required")
        return
    
    try:
        # Initialize orchestrator just to get a discovery agent
        orchestrator = ParallelCategoryOrchestrator()
        await orchestrator.initialize_agents()
        
        # Discover stories from technology category
        print("\n1️⃣ Discovering a single story...")
        
        category = "technology"
        agent = orchestrator.discovery_agents[category]
        
        # Custom prompt for just 1 story
        from agents_v3.utils.enhanced_prompt_loader import enhanced_prompt_loader
        prompt = enhanced_prompt_loader.render_prompt(
            "discovery_category_agent",
            {
                "category_name": "Technology News",
                "search_terms": "AI, artificial intelligence, technology",
                "preferred_sources": "techcrunch.com, wired.com",
                "relevance_criteria": "Major tech developments",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        )
        
        # Add instruction to return just 1 story
        prompt = prompt.replace("Find exactly 10", "Find exactly 1")
        
        conv_id = await agent.start_conversation("discovery")
        response = await agent.send_message(conv_id, prompt)
        await agent.end_conversation(conv_id)
        
        # Parse the story
        stories, errors = orchestrator.discovery_parser.parse_discovery_output(
            response.content, 
            "Technology News"
        )
        
        if not stories:
            print("❌ No story discovered")
            print(f"Errors: {errors}")
            return
        
        story = stories[0]
        print(f"\n✅ Discovered: {story.headline_greek}")
        print(f"   - Source: {story.source_name}")
        print(f"   - Relevance: {story.international_relevance_score}/10")
        
        # Process the single story
        print("\n2️⃣ Processing story with dedicated agents...")
        
        processor = StoryProcessor(story, message_bus)
        
        # Step through each phase
        print("\n📍 Phase 1: Context Gathering")
        await processor._gather_contexts()
        
        print(f"   - Greek context: {'✓' if processor.context_results.get('greek') else '✗'}")
        if processor.context_results.get('greek'):
            print(f"     Length: {len(processor.context_results['greek'])} chars")
            print(f"     Preview: {processor.context_results['greek'][:150]}...")
        
        if story.needs_international_context:
            print(f"   - International context: {'✓' if processor.context_results.get('international') else '✗'}")
            if processor.context_results.get('international'):
                print(f"     Length: {len(processor.context_results['international'])} chars")
                print(f"     Preview: {processor.context_results['international'][:150]}...")
        
        print(f"   - Citations found: {len(processor.citations)}")
        for i, citation in enumerate(processor.citations[:3]):
            print(f"     {i+1}. {citation.get('title', 'No title')} - {citation.get('source_agent', 'unknown')}")
        
        print("\n📍 Phase 2: Fact-Checking")
        factcheck_results = await processor._run_factcheck()
        
        print(f"   - Interrogation complete: {'✓' if factcheck_results else '✗'}")
        if factcheck_results and not factcheck_results.get('error'):
            if factcheck_results.get('verified_claims'):
                print(f"   - Claims verified: {len(factcheck_results['verified_claims'])}")
                for i, claim in enumerate(factcheck_results['verified_claims'][:3]):
                    print(f"     {i+1}. {claim['claim'][:60]}... - {'✓' if claim['verified'] else '✗'}")
        
        print("\n📍 Phase 3: Synthesis")
        # Create synthesis
        synthesis_orchestrator = orchestrator.synthesis_agent
        
        from agents_v3.utils.enhanced_prompt_loader import enhanced_prompt_loader
        prompt = enhanced_prompt_loader.render_prompt(
            "greek_synthesis_agent",
            {
                "story_headline": story.headline_greek,
                "discovery_summary": story.summary,
                "greek_context": processor.context_results.get("greek", ""),
                "international_context": processor.context_results.get("international", ""),
                "factcheck_results": str(factcheck_results)
            }
        )
        
        conv_id = await synthesis_orchestrator.start_conversation("synthesis")
        synthesis_response = await synthesis_orchestrator.send_message(conv_id, prompt)
        await synthesis_orchestrator.end_conversation(conv_id)
        
        print(f"   - Synthesis created: {'✓' if synthesis_response.content else '✗'}")
        print(f"     Length: {len(synthesis_response.content)} chars")
        
        # Cleanup
        await processor._cleanup_agents()
        print("\n📍 Phase 4: Cleanup")
        print("   - Agents cleaned up: ✓")
        
        # Show final results
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        
        print(f"\nStory: {story.headline_greek}")
        print(f"\nCitations collected: {len(processor.citations)}")
        for i, citation in enumerate(processor.citations):
            print(f"  {i+1}. [{citation.get('title', 'No title')}]({citation.get('url', '')})")
            print(f"      Source: {citation.get('source_agent', 'unknown')}")
        
        print(f"\nErrors encountered: {len(processor.errors)}")
        for error in processor.errors:
            print(f"  - {error}")
        
        print(f"\nGreek Synthesis:")
        print("-" * 60)
        print(synthesis_response.content)
        
        # Save detailed results
        output_file = f"single_story_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "story": story.to_dict(),
                "context_results": processor.context_results,
                "factcheck_results": factcheck_results,
                "citations": processor.citations,
                "synthesis": synthesis_response.content,
                "errors": processor.errors
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'orchestrator' in locals():
            await orchestrator.message_bus.stop()


async def test_mock_story():
    """Test with a mock story (no API calls for discovery)"""
    
    print("🧪 Mock Story Test (Faster)")
    print("=" * 60)
    
    # Create a mock story
    mock_story = ParsedStory(
        id=1,
        headline="OpenAI Announces GPT-5 with Reasoning Capabilities",
        headline_greek="Η OpenAI Ανακοινώνει το GPT-5 με Ικανότητες Συλλογισμού",
        summary="OpenAI unveiled GPT-5, featuring advanced reasoning capabilities and improved factual accuracy. The model shows significant improvements in mathematical reasoning and code generation.",
        source_name="TechCrunch",
        source_url="https://techcrunch.com/gpt5-announcement",
        published_date=datetime.now().strftime("%Y-%m-%d"),
        stakeholders=["OpenAI", "Sam Altman", "Microsoft"],
        international_relevance_score=10,
        relevance_reasoning="Major global AI advancement with implications for all industries",
        category="Technology News"
    )
    
    print(f"📰 Mock Story: {mock_story.headline_greek}")
    
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("\n⚠️  No API keys - showing architecture only")
        print("\nArchitecture flow:")
        print("1. StoryProcessor creates dedicated agents")
        print("2. Greek context agent searches for Greek perspectives")
        print("3. International context agent searches globally")
        print("4. Fact-checker interrogates and verifies claims")
        print("5. Synthesis agent creates Greek narrative")
        print("6. All agents cleaned up")
        return
    
    try:
        # Initialize message bus
        await message_bus.start()
        
        # Create story processor
        processor = StoryProcessor(mock_story, message_bus)
        
        print("\n🔄 Processing mock story...")
        result = await processor.process()
        
        print("\n✅ Processing complete!")
        print(f"  - Context agents used: {list(result['context'].keys())}")
        print(f"  - Citations found: {len(result['citations'])}")
        print(f"  - Errors: {len(result['errors'])}")
        
        # Show citations
        if result['citations']:
            print("\n📚 Citations:")
            for i, citation in enumerate(result['citations'][:5]):
                print(f"  {i+1}. {citation.get('title', 'No title')} ({citation.get('source_agent', 'unknown')})")
        
    except Exception as e:
        print(f"\n❌ Mock test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await message_bus.stop()


def main():
    """Main entry point"""
    
    print("🚀 Single Story Test Suite")
    print("=" * 60)
    
    choice = input("\nSelect test:\n1. Test with real story discovery\n2. Test with mock story (faster)\n> ")
    
    if choice == "2":
        asyncio.run(test_mock_story())
    else:
        asyncio.run(test_single_story_detailed())


if __name__ == "__main__":
    main()