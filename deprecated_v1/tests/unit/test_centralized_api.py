#!/usr/bin/env python3
"""
Quick test of centralized API calling
"""

import asyncio
import sys
sys.path.append('.')

async def test_centralized_api():
    try:
        from api.grok_client import GrokClient
        from api.agents.jargon_agent import JargonAgent
        from api.agents.viewpoints_agent import ViewpointsAgent
        
        print('🧪 Testing Centralized API Calling')
        print('=' * 40)
        
        # Create client
        client = GrokClient()
        
        # Test context
        context = {
            'article_text': 'AI and machine learning are transforming technology.',
            'article_url': 'https://example.com/test',
            'session_id': 'test_session',
            'user_tier': 'free'
        }
        
        print('\n1️⃣ Testing JargonAgent (uses base _call_grok)')
        jargon_agent = JargonAgent.create(client)
        
        # Set a shorter timeout for testing
        jargon_agent.config.timeout_seconds = 30
        
        try:
            result = await asyncio.wait_for(jargon_agent.execute(context), timeout=35)
            if result.success:
                print(f'✅ JargonAgent SUCCESS - Tokens: {result.tokens_used}, Time: {result.execution_time_ms}ms')
            else:
                print(f'❌ JargonAgent FAILED: {result.error}')
        except asyncio.TimeoutError:
            print('⏰ JargonAgent TIMEOUT (35s)')
        
        print('\n2️⃣ Testing ViewpointsAgent (uses centralized _call_grok)')
        viewpoints_agent = ViewpointsAgent.create(client)
        
        # Set a shorter timeout for testing
        viewpoints_agent.config.timeout_seconds = 30
        
        try:
            result = await asyncio.wait_for(viewpoints_agent.execute(context), timeout=35)
            if result.success:
                print(f'✅ ViewpointsAgent SUCCESS - Tokens: {result.tokens_used}, Time: {result.execution_time_ms}ms')
            else:
                print(f'❌ ViewpointsAgent FAILED: {result.error}')
        except asyncio.TimeoutError:
            print('⏰ ViewpointsAgent TIMEOUT (35s)')
        
        print('\n✅ Centralized API calling test complete!')
        
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_centralized_api()) 