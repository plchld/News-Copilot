#!/usr/bin/env python3
"""
Simple test of ViewpointsAgent without live search to isolate timeout issues
"""

import asyncio
import sys
sys.path.append('.')

async def test_viewpoints_simple():
    try:
        from api.grok_client import GrokClient
        from api.agents.viewpoints_agent import ViewpointsAgent
        
        print('🧪 Testing ViewpointsAgent (Simple - No Live Search)')
        print('=' * 50)
        
        # Create client and agent
        client = GrokClient()
        agent = ViewpointsAgent.create(client)
        
        # Override the search params to disable live search
        original_build_search_params = agent._build_search_params
        agent._build_search_params = lambda context: None  # Disable search
        
        # Test context
        context = {
            'article_text': 'AI technology is advancing rapidly with new developments.',
            'article_url': 'https://example.com/ai-test',
            'session_id': 'simple_test_session',
            'user_tier': 'free'
        }
        
        # Set shorter timeout
        agent.config.timeout_seconds = 30
        
        print('\n🔍 Testing WITHOUT live search:')
        try:
            result = await asyncio.wait_for(agent.execute(context), timeout=35)
            if result.success:
                print(f'✅ SUCCESS - Tokens: {result.tokens_used}, Time: {result.execution_time_ms}ms')
                print(f'   Data keys: {list(result.data.keys()) if result.data else "None"}')
            else:
                print(f'❌ FAILED: {result.error}')
        except asyncio.TimeoutError:
            print('⏰ TIMEOUT (35s)')
        
        # Restore original search params and test with live search
        agent._build_search_params = original_build_search_params
        
        print('\n🌐 Testing WITH live search:')
        try:
            result = await asyncio.wait_for(agent.execute(context), timeout=60)
            if result.success:
                print(f'✅ SUCCESS - Tokens: {result.tokens_used}, Time: {result.execution_time_ms}ms')
                print(f'   Data keys: {list(result.data.keys()) if result.data else "None"}')
            else:
                print(f'❌ FAILED: {result.error}')
        except asyncio.TimeoutError:
            print('⏰ TIMEOUT (60s) - Live search is slow')
        
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_viewpoints_simple()) 