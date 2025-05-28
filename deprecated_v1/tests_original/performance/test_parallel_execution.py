#!/usr/bin/env python3
"""
Test parallel execution of core agents (Jargon + Viewpoints)
This is how they should run in the optimized architecture
"""

import asyncio
import time
import sys
sys.path.append('.')

async def test_parallel_execution():
    try:
        from api.grok_client import GrokClient
        from api.agents.jargon_agent import JargonAgent
        from api.agents.viewpoints_agent import ViewpointsAgent
        
        print('🚀 Testing PARALLEL Core Agent Execution')
        print('=' * 50)
        
        # Create client
        client = GrokClient()
        
        # Test context
        context = {
            'article_text': 'Artificial intelligence and machine learning are transforming the technology industry with new breakthroughs in neural networks.',
            'article_url': 'https://example.com/ai-article',
            'session_id': 'parallel_test_session',
            'user_tier': 'premium'
        }
        
        # Create agents
        jargon_agent = JargonAgent.create(client)
        viewpoints_agent = ViewpointsAgent.create(client)
        
        # Set reasonable timeouts (ViewpointsAgent needs more time for live search)
        jargon_agent.config.timeout_seconds = 30
        viewpoints_agent.config.timeout_seconds = 60
        
        print('\n📊 SEQUENTIAL vs PARALLEL Comparison')
        print('-' * 40)
        
        # Test 1: Sequential execution (old way)
        print('\n1️⃣ SEQUENTIAL Execution (old way):')
        sequential_start = time.time()
        
        try:
            jargon_result = await asyncio.wait_for(jargon_agent.execute(context), timeout=35)
            jargon_time = time.time() - sequential_start
            print(f'   ✅ Jargon: {jargon_time:.2f}s, {jargon_result.tokens_used} tokens')
        except asyncio.TimeoutError:
            print('   ⏰ Jargon: TIMEOUT')
            jargon_time = 35
        
        try:
            viewpoints_result = await asyncio.wait_for(viewpoints_agent.execute(context), timeout=65)
            viewpoints_time = time.time() - sequential_start - jargon_time
            print(f'   ✅ Viewpoints: {viewpoints_time:.2f}s, {viewpoints_result.tokens_used} tokens')
        except asyncio.TimeoutError:
            print('   ⏰ Viewpoints: TIMEOUT')
            viewpoints_time = 65
        
        sequential_total = time.time() - sequential_start
        print(f'   📈 Sequential Total: {sequential_total:.2f}s')
        
        # Test 2: Parallel execution (optimized way)
        print('\n2️⃣ PARALLEL Execution (optimized way):')
        parallel_start = time.time()
        
        # Execute both agents in parallel
        tasks = [
            asyncio.wait_for(jargon_agent.execute(context), timeout=35),
            asyncio.wait_for(viewpoints_agent.execute(context), timeout=65)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            parallel_total = time.time() - parallel_start
            
            # Process results
            jargon_result, viewpoints_result = results
            
            if isinstance(jargon_result, Exception):
                print(f'   ❌ Jargon: {type(jargon_result).__name__}')
            else:
                print(f'   ✅ Jargon: {jargon_result.tokens_used} tokens')
            
            if isinstance(viewpoints_result, Exception):
                print(f'   ❌ Viewpoints: {type(viewpoints_result).__name__}')
            else:
                print(f'   ✅ Viewpoints: {viewpoints_result.tokens_used} tokens')
            
            print(f'   🚀 Parallel Total: {parallel_total:.2f}s')
            
            # Calculate improvement
            if sequential_total > 0 and parallel_total > 0:
                improvement = ((sequential_total - parallel_total) / sequential_total) * 100
                speedup = sequential_total / parallel_total
                print(f'\n📈 PERFORMANCE IMPROVEMENT:')
                print(f'   ⚡ {improvement:.1f}% faster')
                print(f'   🔥 {speedup:.1f}x speedup')
                print(f'   ⏱️  Saved {sequential_total - parallel_total:.2f} seconds')
            
        except Exception as e:
            print(f'   ❌ Parallel execution failed: {str(e)}')
        
        print('\n✅ This is how the optimized architecture should work!')
        print('   Core agents run in PARALLEL for immediate user feedback')
        
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parallel_execution()) 