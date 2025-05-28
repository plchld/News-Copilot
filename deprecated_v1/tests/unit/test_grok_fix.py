#!/usr/bin/env python3
"""
Test script to verify Grok API fix
"""

import asyncio
import sys
sys.path.append('.')

async def test_grok_call():
    try:
        from api.grok_client import GrokClient
        from api.agents.jargon_agent import JargonAgent
        
        print('🧪 Testing Grok API call without response_format...')
        
        # Create client and agent
        client = GrokClient()
        agent = JargonAgent.create(client)
        
        # Test context
        context = {
            'article_text': 'This is a test article about artificial intelligence and machine learning.',
            'article_url': 'https://example.com/test',
            'session_id': 'test_session',
            'user_tier': 'free'
        }
        
        # Try to execute
        result = await agent.execute(context)
        
        if result.success:
            print('✅ Grok API call successful!')
            print(f'   Tokens used: {result.tokens_used}')
            print(f'   Execution time: {result.execution_time_ms}ms')
            print(f'   Data keys: {list(result.data.keys()) if result.data else "None"}')
        else:
            print(f'❌ Grok API call failed: {result.error}')
            
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')

if __name__ == "__main__":
    asyncio.run(test_grok_call()) 