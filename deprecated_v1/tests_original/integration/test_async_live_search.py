#!/usr/bin/env python3
"""
Focused test for xAI Asynchronous Live Search
Tests concurrent live search requests using AsyncOpenAI
"""

import asyncio
import os
from asyncio import Semaphore
from typing import List, Dict, Any
from openai import AsyncOpenAI
from datetime import datetime, timedelta


# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1"

if not XAI_API_KEY:
    print("❌ XAI_API_KEY environment variable not set!")
    print("Please set it with: export XAI_API_KEY='your-api-key'")
    exit(1)

# Initialize async client
async_client = AsyncOpenAI(
    api_key=XAI_API_KEY,
    base_url=XAI_BASE_URL
)


async def send_live_search_request(sem: Semaphore, query: str, search_params: Dict[str, Any]) -> dict:
    """Send a single live search request to xAI with semaphore control."""
    async with sem:
        print(f"🔍 Sending async live search: {query[:60]}...")
        return await async_client.chat.completions.create(
            model="grok-3-latest",
            messages=[{"role": "user", "content": query}],
            extra_body={"search_parameters": search_params}
        )


async def process_live_search_requests(queries_and_params: List[tuple], max_concurrent: int = 3) -> List[dict]:
    """Process multiple live search requests with controlled concurrency."""
    sem = Semaphore(max_concurrent)
    tasks = [send_live_search_request(sem, query, params) for query, params in queries_and_params]
    return await asyncio.gather(*tasks)


async def test_async_live_search():
    """Test asynchronous live search requests with various configurations."""
    print("🔍 ASYNCHRONOUS LIVE SEARCH TEST")
    print("="*60)
    
    # Define diverse search queries with different parameters
    queries_and_params = [
        (
            "What are the latest AI breakthroughs and developments this week?",
            {
                "mode": "on",
                "sources": [{"type": "web"}, {"type": "news"}],
                "return_citations": True,
                "max_search_results": 8
            }
        ),
        (
            "What's trending on X about technology and startups today?",
            {
                "mode": "on",
                "sources": [{"type": "x"}],
                "return_citations": True,
                "max_search_results": 5
            }
        ),
        (
            "Latest cryptocurrency and blockchain news from reliable sources",
            {
                "mode": "on",
                "sources": [{"type": "news", "excluded_websites": ["reddit.com", "twitter.com"]}],
                "return_citations": True,
                "max_search_results": 6
            }
        ),
        (
            "What are people saying about climate change solutions this week?",
            {
                "mode": "on",
                "sources": [{"type": "web"}, {"type": "x"}],
                "return_citations": True,
                "from_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "max_search_results": 7
            }
        ),
        (
            "Recent developments in space exploration and SpaceX",
            {
                "mode": "on",
                "sources": [
                    {"type": "news", "country": "US"},
                    {"type": "x", "x_handles": ["spacex", "elonmusk"]}
                ],
                "return_citations": True,
                "max_search_results": 5
            }
        )
    ]
    
    print(f"📝 Testing {len(queries_and_params)} concurrent live search requests")
    print(f"⚡ Max concurrent requests: 3")
    print(f"🕐 Starting at: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)
    
    start_time = datetime.now()
    
    try:
        responses = await process_live_search_requests(queries_and_params, max_concurrent=3)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Async live search completed in {duration:.2f} seconds")
        print("=" * 60)
        
        for i, response in enumerate(responses):
            query = queries_and_params[i][0]
            search_params = queries_and_params[i][1]
            content = response.choices[0].message.content
            
            # Extract citations if available
            citations = []
            if hasattr(response, 'citations') and response.citations:
                citations = response.citations
            elif hasattr(response.choices[0], 'citations') and response.choices[0].citations:
                citations = response.choices[0].citations
            
            print(f"\n📄 RESULT {i+1}")
            print(f"❓ Query: {query}")
            print(f"🔧 Sources: {[src['type'] for src in search_params.get('sources', [{'type': 'web'}, {'type': 'x'}])]}")
            print(f"📊 Max results: {search_params.get('max_search_results', 'default')}")
            if 'from_date' in search_params:
                print(f"📅 Date filter: from {search_params['from_date']}")
            print("-" * 50)
            print(f"📝 Response: {content[:300]}...")
            print(f"🔗 Citations found: {len(citations)}")
            
            if citations:
                print("📎 Top citations:")
                for j, citation in enumerate(citations[:3]):  # Show first 3 citations
                    print(f"   {j+1}. {citation}")
            print()
            
    except Exception as e:
        print(f"❌ Async live search failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run the async live search test."""
    print("🧪 xAI Asynchronous Live Search Test")
    print("Testing concurrent live search capabilities with various parameters")
    print()
    
    await test_async_live_search()
    
    print("\n" + "="*60)
    print("✨ Async live search test completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main()) 