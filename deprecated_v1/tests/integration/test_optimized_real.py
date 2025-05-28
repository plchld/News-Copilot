#!/usr/bin/env python3
"""
Test the optimized architecture with real Grok API
"""

import asyncio
import sys
import time
sys.path.append('.')

async def test_optimized_real():
    try:
        from api.grok_client import GrokClient
        from api.agents.optimized_coordinator import OptimizedAgentCoordinator, OptimizedCoordinatorConfig
        
        print('🚀 Testing Optimized Architecture with Real Grok API')
        print('=' * 60)
        
        # Create coordinator with real client
        client = GrokClient()
        config = OptimizedCoordinatorConfig(
            core_timeout_seconds=60,
            on_demand_timeout_seconds=120,
            cache_ttl_minutes=60
        )
        coordinator = OptimizedAgentCoordinator(client, config)
        
        # Test article
        article_url = "https://example.com/test-article"
        article_text = """
        Artificial intelligence (AI) has made significant breakthroughs in recent years, 
        particularly in machine learning and natural language processing. These advances 
        have implications for various stakeholders including technology companies, 
        researchers, policymakers, and the general public.
        """
        
        user_context = {
            'user_id': 'test_user',
            'user_tier': 'premium',
            'session_id': 'real_test_session'
        }
        
        print('\n👤 USER ACTION: Testing Core Analysis')
        print('-' * 40)
        
        # Test core analysis
        start_time = time.time()
        core_result = await coordinator.analyze_core(
            article_url=article_url,
            article_text=article_text,
            user_context=user_context
        )
        core_time = time.time() - start_time
        
        if core_result['success']:
            print(f'✅ Core Analysis SUCCESS ({core_time:.2f}s)')
            print(f'   Session ID: {core_result["session_id"]}')
            print(f'   Successful analyses: {core_result["metadata"]["successful_analyses"]}/2')
            print(f'   Total tokens: {core_result["metadata"]["total_tokens_used"]}')
            
            # Test on-demand analysis
            session_id = core_result['session_id']
            
            print(f'\n👤 USER ACTION: Testing On-Demand Analysis')
            print('-' * 40)
            
            # Test fact-check
            start_time = time.time()
            fact_check_result = await coordinator.analyze_on_demand(
                analysis_type='fact-check',
                session_id=session_id,
                user_context={'user_id': 'test_user', 'user_tier': 'premium'}
            )
            fact_check_time = time.time() - start_time
            
            if fact_check_result['success']:
                print(f'✅ Fact-Check SUCCESS ({fact_check_time:.2f}s)')
                print(f'   Cache hit: {fact_check_result["metadata"]["cache_hit"]}')
                print(f'   Tokens used: {fact_check_result["metadata"]["tokens_used"]}')
            else:
                print(f'❌ Fact-Check FAILED: {fact_check_result["error"]}')
            
            # Test cache stats
            cache_stats = await coordinator.get_cache_stats()
            print(f'\n📊 Cache Stats:')
            print(f'   Cached sessions: {cache_stats["cached_sessions"]}')
            print(f'   Cache size: {cache_stats["cache_size_mb"]:.2f} MB')
            
        else:
            print(f'❌ Core Analysis FAILED: {core_result.get("error", "Unknown error")}')
            
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimized_real()) 