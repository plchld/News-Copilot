#!/usr/bin/env python3
"""Test Grok API connectivity"""

import os
import sys
import asyncio

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.grok_client import GrokClient


async def test_grok_api():
    """Test basic Grok API call"""
    
    print("Testing Grok API connectivity...")
    
    # Check API key
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("✗ XAI_API_KEY not set!")
        return
    else:
        print(f"✓ API Key found: {api_key[:10]}...")
    
    try:
        # Create client
        client = GrokClient()
        print("✓ GrokClient created")
        
        # Test sync API
        print("\nTesting synchronous API...")
        response = client.client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello, I am working!' in exactly 5 words"}
            ],
            temperature=0
        )
        
        print(f"✓ Sync API response: {response.choices[0].message.content}")
        
        # Test async API
        print("\nTesting asynchronous API...")
        async_response = await client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {"role": "user", "content": "Say 'Async is working too!' in exactly 4 words"}
            ],
            temperature=0
        )
        
        print(f"✓ Async API response: {async_response.choices[0].message.content}")
        
        # Test with search parameters
        print("\nTesting with search parameters...")
        search_params = {
            "mode": "on",
            "sources": [{"type": "web"}, {"type": "news"}],
            "max_results": 5
        }
        
        search_response = await client.async_client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "user", "content": "What is the weather today in Athens, Greece? Answer in one sentence."}
            ],
            temperature=0,
            extra_body={"search_parameters": search_params}
        )
        
        print(f"✓ Search API response: {search_response.choices[0].message.content}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_grok_api())