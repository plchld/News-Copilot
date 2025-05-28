#!/usr/bin/env python3
"""Test if there's an async handling issue"""

import asyncio
import os
import sys

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

async def test_coordinator():
    """Test the coordinator directly"""
    
    print("Testing coordinator analyze_core...")
    
    try:
        from api.agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, OptimizedCoordinatorConfig as CoordinatorConfig
        from api.grok_client import GrokClient
        from api.article_extractor import fetch_text
        
        # Create client and coordinator
        grok_client = GrokClient()
        config = CoordinatorConfig(
            core_parallel_limit=2,
            core_timeout_seconds=60,
            on_demand_timeout_seconds=120,
            cache_ttl_minutes=60,
            enable_result_caching=True,
            enable_context_caching=True
        )
        coordinator = AgentCoordinator(grok_client, config)
        
        # Test article
        article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
        
        print(f"Fetching article: {article_url}")
        article_text = fetch_text(article_url)
        print(f"✓ Article fetched: {len(article_text)} chars")
        
        # Context
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': 'free',
            'user_id': 'test'
        }
        
        print("\nCalling coordinator.analyze_core...")
        
        # Call with timeout
        try:
            results = await asyncio.wait_for(
                coordinator.analyze_core(
                    article_url=article_url,
                    article_text=article_text,
                    user_context=context
                ),
                timeout=30.0
            )
            
            print(f"✓ Got results: {type(results)}")
            print(f"  Keys: {list(results.keys())}")
            print(f"  Success: {results.get('success')}")
            
            if not results.get('success'):
                print(f"  Error: {results.get('error')}")
                print(f"  Errors: {results.get('errors')}")
                
        except asyncio.TimeoutError:
            print("✗ Timeout after 30 seconds!")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_coordinator())