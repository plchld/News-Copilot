#!/usr/bin/env python3
"""
Timeout Investigation Debug Script
Specifically designed to understand why core analysis is timing out
"""

import asyncio
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.grok_client import GrokClient
from api.agents.optimized_coordinator import OptimizedAgentCoordinator, OptimizedCoordinatorConfig
from api.agents.viewpoints_agent import ViewpointsAgent
from api.agents.jargon_agent import JargonAgent
from api.agents.debug_framework import AgentDebugger, DebugLevel
from api.article_extractor import fetch_text


async def test_individual_agents(article_url: str, article_text: str):
    """Test individual agents to see which one is causing the timeout"""
    print("\n" + "="*80)
    print("🔍 TESTING INDIVIDUAL AGENTS")
    print("="*80)
    
    grok_client = GrokClient()
    
    # Test context
    context = {
        'article_text': article_text,
        'article_url': article_url,
        'session_id': f'debug_{datetime.now().timestamp()}',
        'user_tier': 'free',
        'user_id': 'debug_user'
    }
    
    # Test Jargon Agent
    print("\n1️⃣ Testing JARGON Agent...")
    jargon_start = time.time()
    try:
        jargon_agent = JargonAgent.create(grok_client)
        jargon_debugger = AgentDebugger(jargon_agent, DebugLevel.VERBOSE)
        
        jargon_result, jargon_trace = await asyncio.wait_for(
            jargon_debugger.execute_with_trace(context),
            timeout=60  # 60 second timeout
        )
        
        jargon_time = time.time() - jargon_start
        print(f"   ✅ Jargon completed in {jargon_time:.2f}s")
        print(f"   📊 Success: {jargon_result.success}")
        print(f"   🪙 Tokens: {jargon_result.tokens_used}")
        
        if not jargon_result.success:
            print(f"   ❌ Error: {jargon_result.error}")
            
    except asyncio.TimeoutError:
        jargon_time = time.time() - jargon_start
        print(f"   ⏰ Jargon TIMED OUT after {jargon_time:.2f}s")
    except Exception as e:
        jargon_time = time.time() - jargon_start
        print(f"   💥 Jargon FAILED after {jargon_time:.2f}s: {e}")
    
    # Test Viewpoints Agent
    print("\n2️⃣ Testing VIEWPOINTS Agent...")
    viewpoints_start = time.time()
    try:
        viewpoints_agent = ViewpointsAgent.create(grok_client)
        viewpoints_debugger = AgentDebugger(viewpoints_agent, DebugLevel.VERBOSE)
        
        viewpoints_result, viewpoints_trace = await asyncio.wait_for(
            viewpoints_debugger.execute_with_trace(context),
            timeout=60  # 60 second timeout
        )
        
        viewpoints_time = time.time() - viewpoints_start
        print(f"   ✅ Viewpoints completed in {viewpoints_time:.2f}s")
        print(f"   📊 Success: {viewpoints_result.success}")
        print(f"   🪙 Tokens: {viewpoints_result.tokens_used}")
        
        if not viewpoints_result.success:
            print(f"   ❌ Error: {viewpoints_result.error}")
            
    except asyncio.TimeoutError:
        viewpoints_time = time.time() - viewpoints_start
        print(f"   ⏰ Viewpoints TIMED OUT after {viewpoints_time:.2f}s")
    except Exception as e:
        viewpoints_time = time.time() - viewpoints_start
        print(f"   💥 Viewpoints FAILED after {viewpoints_time:.2f}s: {e}")


async def test_coordinator_with_shorter_timeout(article_url: str, article_text: str):
    """Test the coordinator with progressively shorter timeouts to find the breaking point"""
    print("\n" + "="*80)
    print("🎯 TESTING COORDINATOR WITH DIFFERENT TIMEOUTS")
    print("="*80)
    
    grok_client = GrokClient()
    
    context = {
        'user_tier': 'free',
        'user_id': 'debug_user'
    }
    
    # Test with different timeout values
    timeout_values = [30, 60, 90, 120]
    
    for timeout_seconds in timeout_values:
        print(f"\n🕐 Testing with {timeout_seconds}s timeout...")
        
        config = OptimizedCoordinatorConfig(
            core_timeout_seconds=timeout_seconds,
            on_demand_timeout_seconds=timeout_seconds + 30
        )
        
        coordinator = OptimizedAgentCoordinator(grok_client, config)
        
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                coordinator.analyze_core(
                    article_url=article_url,
                    article_text=article_text,
                    user_context=context
                ),
                timeout=timeout_seconds + 10  # Add 10s buffer for coordinator overhead
            )
            
            elapsed = time.time() - start_time
            print(f"   ✅ SUCCESS in {elapsed:.2f}s")
            print(f"   📊 Core success: {result.get('success')}")
            
            if result.get('success'):
                metadata = result.get('metadata', {})
                print(f"   ⏱️  Execution time: {metadata.get('execution_time_seconds', 0):.2f}s")
                print(f"   🪙 Total tokens: {metadata.get('total_tokens_used', 0)}")
                print(f"   ✅ Successful analyses: {metadata.get('successful_analyses', 0)}/2")
                break  # Success, no need to test longer timeouts
            else:
                print(f"   ❌ Failed: {result.get('error')}")
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"   ⏰ TIMEOUT after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   💥 ERROR after {elapsed:.2f}s: {e}")


async def test_simple_grok_call():
    """Test a simple Grok API call to ensure basic connectivity"""
    print("\n" + "="*80)
    print("🌐 TESTING BASIC GROK API CONNECTIVITY")
    print("="*80)
    
    try:
        grok_client = GrokClient()
        
        print("📡 Making simple API call...")
        start_time = time.time()
        
        # Simple test prompt
        test_prompt = "Explain what artificial intelligence is in one sentence."
        
        response = await asyncio.wait_for(
            grok_client.async_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": test_prompt}]
            ),
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ API call successful in {elapsed:.2f}s")
        print(f"   📝 Response: {response.choices[0].message.content[:100]}...")
        print(f"   🪙 Tokens: {response.usage.total_tokens if hasattr(response, 'usage') else 'unknown'}")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"   ⏰ API call timed out after {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   💥 API call failed after {elapsed:.2f}s: {e}")


async def main():
    """Main debug investigation"""
    # The problematic article from your logs
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print("🔍 TIMEOUT INVESTIGATION DEBUG")
    print("="*80)
    print(f"📰 Article: {article_url}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Extract article
    print("\n📥 Extracting article content...")
    try:
        article_text = fetch_text(article_url)
        print(f"   ✅ Article extracted successfully")
        print(f"   📏 Length: {len(article_text)} characters")
        print(f"   📝 First 200 chars: {article_text[:200]}...")
    except Exception as e:
        print(f"   ❌ Failed to extract article: {e}")
        return
    
    # Step 2: Test basic API connectivity
    await test_simple_grok_call()
    
    # Step 3: Test individual agents
    await test_individual_agents(article_url, article_text)
    
    # Step 4: Test coordinator with different timeouts
    await test_coordinator_with_shorter_timeout(article_url, article_text)
    
    print("\n" + "="*80)
    print("🏁 INVESTIGATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv('XAI_API_KEY'):
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    asyncio.run(main()) 