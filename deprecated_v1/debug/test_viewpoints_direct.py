#!/usr/bin/env python3
"""Direct test of viewpoints agent"""

import asyncio
import os
import sys

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.agents.viewpoints_agent import ViewpointsAgent
from api.grok_client import GrokClient
from api.article_extractor import fetch_text


async def test_viewpoints():
    """Test viewpoints agent directly"""
    
    # Check API key
    if not os.getenv('XAI_API_KEY'):
        print("ERROR: XAI_API_KEY not set")
        return
    
    # Initialize client
    print("Creating Grok client...")
    grok_client = GrokClient()
    
    # Create agent
    print("Creating ViewpointsAgent...")
    agent = ViewpointsAgent.create(grok_client)
    
    # Test URL
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    # Fetch article
    print(f"\nFetching article from: {article_url}")
    try:
        article_text = fetch_text(article_url)
        print(f"✓ Article fetched: {len(article_text)} characters")
    except Exception as e:
        print(f"✗ Error fetching article: {e}")
        return
    
    # Prepare context
    context = {
        'article_text': article_text,
        'article_url': article_url,
        'session_id': 'test_direct',
        'user_tier': 'premium'
    }
    
    # Test search params
    print("\nTesting search parameters...")
    search_params = agent._build_search_params(context)
    if search_params:
        print(f"✓ Search params built:")
        print(f"  - Sources: {len(search_params.get('sources', []))}")
        print(f"  - Excluded domains: {search_params.get('excluded_websites_map', {}).get('domains', [])[:3]}...")
    else:
        print("✗ No search params returned")
    
    # Execute agent
    print("\nExecuting ViewpointsAgent...")
    print("This may take 10-30 seconds...")
    
    try:
        result = await agent.execute(context)
        
        print(f"\n{'='*60}")
        print("RESULT:")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Execution time: {result.execution_time_ms}ms")
        print(f"Model used: {result.model_used.value if result.model_used else 'unknown'}")
        
        if result.success and result.data:
            viewpoints = result.data.get('viewpoints', [])
            print(f"\nViewpoints found: {len(viewpoints)}")
            
            if viewpoints:
                print("\nFirst 3 viewpoints:")
                for i, vp in enumerate(viewpoints[:3], 1):
                    print(f"\n{i}. {vp[:200]}{'...' if len(vp) > 200 else ''}")
            else:
                print("\n✗ No viewpoints in response!")
                print(f"Full data: {result.data}")
        else:
            print(f"\nError: {result.error}")
            
    except Exception as e:
        print(f"\n✗ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_viewpoints())