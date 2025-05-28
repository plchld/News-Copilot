#!/usr/bin/env python3
"""
Test the timeout fixes
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.grok_client import GrokClient
from api.agents.optimized_coordinator import OptimizedAgentCoordinator, OptimizedCoordinatorConfig
from api.agents.viewpoints_agent import ViewpointsAgent
from api.article_extractor import fetch_text


async def test_optimized_viewpoints():
    """Test the optimized ViewpointsAgent"""
    print("🔧 Testing Optimized ViewpointsAgent")
    print("="*60)
    
    # The problematic article
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    # Extract article
    print("📥 Extracting article...")
    article_text = fetch_text(article_url)
    print(f"   ✅ Article extracted ({len(article_text)} chars)")
    
    # Test context
    context = {
        'article_text': article_text,
        'article_url': article_url,
        'session_id': f'test_{datetime.now().timestamp()}',
        'user_tier': 'free',
        'user_id': 'test_user'
    }
    
    # Test ViewpointsAgent directly
    print("\n🎯 Testing ViewpointsAgent directly...")
    grok_client = GrokClient()
    viewpoints_agent = ViewpointsAgent.create(grok_client)
    
    start_time = time.time()
    try:
        result = await asyncio.wait_for(
            viewpoints_agent.execute(context),
            timeout=90  # 90 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ ViewpointsAgent completed in {elapsed:.2f}s")
        print(f"   📊 Success: {result.success}")
        print(f"   🪙 Tokens: {result.tokens_used}")
        
        if result.success and result.data:
            viewpoints = result.data.get('viewpoints', [])
            print(f"   📝 Found {len(viewpoints)} viewpoints")
        elif result.error:
            print(f"   ❌ Error: {result.error}")
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"   ⏰ ViewpointsAgent still timed out after {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   💥 ViewpointsAgent failed after {elapsed:.2f}s: {e}")


async def test_optimized_coordinator():
    """Test the optimized coordinator"""
    print("\n🎯 Testing Optimized Coordinator")
    print("="*60)
    
    # The problematic article
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    # Extract article
    print("📥 Extracting article...")
    article_text = fetch_text(article_url)
    print(f"   ✅ Article extracted ({len(article_text)} chars)")
    
    # Test coordinator
    grok_client = GrokClient()
    config = OptimizedCoordinatorConfig(
        core_timeout_seconds=150,  # New timeout
        on_demand_timeout_seconds=120
    )
    coordinator = OptimizedAgentCoordinator(grok_client, config)
    
    context = {
        'user_tier': 'free',
        'user_id': 'test_user'
    }
    
    start_time = time.time()
    try:
        result = await asyncio.wait_for(
            coordinator.analyze_core(
                article_url=article_url,
                article_text=article_text,
                user_context=context
            ),
            timeout=160  # 160 second timeout with buffer
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ Coordinator completed in {elapsed:.2f}s")
        print(f"   📊 Success: {result.get('success')}")
        
        if result.get('success'):
            metadata = result.get('metadata', {})
            print(f"   ⏱️  Execution time: {metadata.get('execution_time_seconds', 0):.2f}s")
            print(f"   🪙 Total tokens: {metadata.get('total_tokens_used', 0)}")
            print(f"   ✅ Successful analyses: {metadata.get('successful_analyses', 0)}/2")
            
            results = result.get('results', {})
            print(f"   📝 Jargon result: {'✅' if results.get('jargon') else '❌'}")
            print(f"   📝 Viewpoints result: {'✅' if results.get('viewpoints') else '❌'}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"   ⏰ Coordinator timed out after {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   💥 Coordinator failed after {elapsed:.2f}s: {e}")


async def main():
    """Main test function"""
    print("🧪 TESTING TIMEOUT FIXES")
    print("="*80)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual ViewpointsAgent
    await test_optimized_viewpoints()
    
    # Test coordinator
    await test_optimized_coordinator()
    
    print("\n" + "="*80)
    print("🏁 TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv('XAI_API_KEY'):
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    asyncio.run(main()) 