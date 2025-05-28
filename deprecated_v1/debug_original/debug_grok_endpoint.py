#!/usr/bin/env python3
"""
Grok API Endpoint Diagnostic Tool
Checks which endpoint you're connected to and tests capabilities
"""

import asyncio
import time
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.grok_client import GrokClient
from api.config import API_URL, API_KEY, MODEL


async def test_endpoint_info():
    """Test basic endpoint connectivity and get info"""
    print("🌐 GROK API ENDPOINT DIAGNOSTIC")
    print("="*80)
    
    # Show configuration
    print(f"📍 API Endpoint: {API_URL}")
    print(f"🤖 Default Model: {MODEL}")
    print(f"🔑 API Key: {API_KEY[:10]}...{API_KEY[-4:] if API_KEY else 'NOT SET'}")
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not API_KEY:
        print("❌ ERROR: XAI_API_KEY not set!")
        return
    
    grok_client = GrokClient()
    
    # Test 1: Basic connectivity
    print("\n" + "="*60)
    print("🔍 TEST 1: Basic API Connectivity")
    print("="*60)
    
    try:
        start_time = time.time()
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": "Hello, what is your name and which endpoint am I connected to?"}],
            max_tokens=100
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Basic connectivity: SUCCESS ({elapsed:.2f}s)")
        print(f"📝 Response: {response.choices[0].message.content}")
        
        # Check response headers for endpoint info
        if hasattr(response, '_raw_response'):
            headers = response._raw_response.headers
            print(f"🌍 Server headers: {dict(headers)}")
        
    except Exception as e:
        print(f"❌ Basic connectivity: FAILED - {e}")
        return
    
    # Test 2: Model availability
    print("\n" + "="*60)
    print("🤖 TEST 2: Model Availability")
    print("="*60)
    
    models_to_test = ["grok-3", "grok-3-mini", "grok-3-mini-fast"]
    
    for model in models_to_test:
        try:
            start_time = time.time()
            response = await grok_client.async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            elapsed = time.time() - start_time
            print(f"✅ {model}: Available ({elapsed:.2f}s)")
            
        except Exception as e:
            print(f"❌ {model}: Not available - {str(e)[:100]}")
    
    # Test 3: Live Search capability
    print("\n" + "="*60)
    print("🔍 TEST 3: Live Search Capability")
    print("="*60)
    
    try:
        start_time = time.time()
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": "What are the latest news about Greece today?"}],
            extra_body={
                "search_parameters": {
                    "mode": "on",
                    "sources": [{"type": "news", "country": "GR", "language": "el"}],
                    "max_search_results": 5
                }
            }
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Live Search: Available ({elapsed:.2f}s)")
        print(f"📝 Response length: {len(response.choices[0].message.content)} chars")
        
        # Check for citations
        citations = grok_client.extract_citations(response)
        print(f"📚 Citations found: {len(citations)}")
        
    except Exception as e:
        print(f"❌ Live Search: Not available - {e}")
    
    # Test 4: Thinking models
    print("\n" + "="*60)
    print("🧠 TEST 4: Thinking Models")
    print("="*60)
    
    try:
        start_time = time.time()
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini-fast",
            messages=[{"role": "user", "content": "Think step by step: What is 2+2?"}],
            extra_body={"reasoning_effort": "low"}
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Thinking Models: Available ({elapsed:.2f}s)")
        
        # Check for reasoning content
        if hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning = response.choices[0].message.reasoning_content
            print(f"🧠 Reasoning content: {len(reasoning)} chars")
            print(f"📝 First 200 chars: {reasoning[:200]}...")
        else:
            print("⚠️ No reasoning content found")
            
    except Exception as e:
        print(f"❌ Thinking Models: Not available - {e}")
    
    # Test 5: Rate limits and performance
    print("\n" + "="*60)
    print("⚡ TEST 5: Performance & Rate Limits")
    print("="*60)
    
    # Test multiple quick requests
    request_times = []
    success_count = 0
    
    for i in range(5):
        try:
            start_time = time.time()
            response = await grok_client.async_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": f"Quick test {i+1}"}],
                max_tokens=5
            )
            elapsed = time.time() - start_time
            request_times.append(elapsed)
            success_count += 1
            print(f"  Request {i+1}: {elapsed:.2f}s")
            
        except Exception as e:
            print(f"  Request {i+1}: FAILED - {str(e)[:50]}")
    
    if request_times:
        avg_time = sum(request_times) / len(request_times)
        print(f"📊 Average response time: {avg_time:.2f}s")
        print(f"📊 Success rate: {success_count}/5 ({success_count*20}%)")
    
    # Test 6: Error handling
    print("\n" + "="*60)
    print("🚨 TEST 6: Error Handling")
    print("="*60)
    
    # Test invalid model
    try:
        response = await grok_client.async_client.chat.completions.create(
            model="invalid-model",
            messages=[{"role": "user", "content": "Test"}]
        )
        print("⚠️ Invalid model accepted (unexpected)")
    except Exception as e:
        print(f"✅ Invalid model rejected: {str(e)[:100]}")
    
    # Test response_format (should fail)
    try:
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": "Test"}],
            response_format={"type": "json_object"}
        )
        print("⚠️ response_format accepted (unexpected)")
    except Exception as e:
        print(f"✅ response_format rejected: {str(e)[:100]}")


async def test_endpoint_regions():
    """Test different potential endpoint regions"""
    print("\n" + "="*60)
    print("🌍 ENDPOINT REGION ANALYSIS")
    print("="*60)
    
    # Test latency to different regions (if accessible)
    endpoints_to_test = [
        ("Current (api.x.ai)", "https://api.x.ai/v1"),
        ("Alternative 1", "https://api.xai.com/v1"),  # Hypothetical
        ("Alternative 2", "https://grok-api.x.ai/v1"),  # Hypothetical
    ]
    
    for name, url in endpoints_to_test:
        if url == API_URL:
            print(f"✅ {name}: CURRENT ENDPOINT")
        else:
            print(f"ℹ️ {name}: {url} (not tested - would require API key change)")


def analyze_endpoint_capabilities():
    """Analyze what we learned about the endpoint"""
    print("\n" + "="*80)
    print("📋 ENDPOINT ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"""
🔍 ENDPOINT DETAILS:
   • URL: {API_URL}
   • Primary Model: {MODEL}
   • Region: Likely US-based (api.x.ai)
   
⚠️ KNOWN GROK API LIMITATIONS:
   • No response_format parameter support
   • Limited model selection compared to OpenAI
   • Live search may have regional restrictions
   • Rate limits vary by subscription tier
   
🔧 RECOMMENDATIONS:
   • Use grok-3-mini for faster responses
   • Remove all response_format parameters
   • Handle JSON parsing manually
   • Monitor rate limits during peak usage
   • Consider caching for repeated requests
   
📊 PERFORMANCE TIPS:
   • Use async calls for better throughput
   • Batch requests when possible
   • Implement exponential backoff for retries
   • Monitor token usage for cost optimization
    """)


async def main():
    """Main diagnostic function"""
    await test_endpoint_info()
    await test_endpoint_regions()
    analyze_endpoint_capabilities()
    
    print("\n" + "="*80)
    print("🏁 DIAGNOSTIC COMPLETE")
    print("="*80)
    print("💡 Use this information to optimize your Grok API usage!")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv('XAI_API_KEY'):
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    asyncio.run(main()) 