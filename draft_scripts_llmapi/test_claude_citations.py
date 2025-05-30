#!/usr/bin/env python3
"""
Test script to verify Claude citations are properly extracted
"""

import asyncio
import json
from claude_search import ClaudeSearchClient

async def test_citations():
    """Test citation extraction from Claude search"""
    
    print("🧪 Testing Claude Citation Extraction")
    print("=" * 60)
    
    # Initialize client
    client = ClaudeSearchClient()
    
    # Simple test query
    system_prompt = "You are a helpful assistant that searches for information."
    user_prompt = "Find the latest news about artificial intelligence developments in 2025. Include citations."
    
    try:
        # Perform search
        result = await client.search(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            region="United States"
        )
        
        print("\n📊 Results Summary:")
        print(f"- Content length: {len(result['content'])} characters")
        print(f"- Citations found: {len(result['citations'])}")
        print(f"- Search count: {result['search_count']}")
        print(f"- Model used: {result['model']}")
        
        if result['citations']:
            print("\n📚 Citations extracted:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"\n{i}. Citation:")
                print(f"   Title: {citation['title']}")
                print(f"   URL: {citation['url']}")
                print(f"   Cited text: {citation['cited_text'][:100]}..." if citation['cited_text'] else "   Cited text: None")
                print(f"   Has encrypted index: {'Yes' if citation['encrypted_index'] else 'No'}")
        else:
            print("\n⚠️  No citations found in response")
        
        # Save full result for inspection
        with open('test_citations_result.json', 'w', encoding='utf-8') as f:
            json.dump({
                'content': result['content'][:500] + '...' if len(result['content']) > 500 else result['content'],
                'citations': result['citations'],
                'search_count': result['search_count'],
                'model': result['model']
            }, f, ensure_ascii=False, indent=2)
        
        print("\n✅ Full results saved to test_citations_result.json")
        
    except Exception as e:
        print(f"\n❌ Error testing citations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_citations())