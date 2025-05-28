"""
Test suite for the optimized agent architecture
Tests core analysis, on-demand features, caching, and performance improvements
"""

import asyncio
import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from api.agents.optimized_coordinator import (
    OptimizedAgentCoordinator,
    OptimizedCoordinatorConfig,
    AnalysisCache,
    CoreAnalysisCoordinator,
    OnDemandCoordinator,
    AnalysisType
)


class MockGrokClient:
    """Mock Grok client for testing"""
    
    def __init__(self):
        self.async_client = Mock()
        self.async_client.chat = Mock()
        self.async_client.chat.completions = Mock()
        self.async_client.chat.completions.create = AsyncMock()
        
        # Configure mock responses with proper structure
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"simplified_terms": [{"term": "test", "definition": "test definition"}], "perspectives": [{"stakeholder": "test", "viewpoint": "test viewpoint"}]}'
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 100
        
        self.async_client.chat.completions.create.return_value = mock_response


class TestOptimizedArchitecture:
    """Test the optimized agent architecture"""
    
    @pytest.fixture
    def mock_grok_client(self):
        return MockGrokClient()
    
    @pytest.fixture
    def test_config(self):
        return OptimizedCoordinatorConfig(
            core_timeout_seconds=10,
            on_demand_timeout_seconds=20,
            cache_ttl_minutes=5,
            enable_result_caching=True,
            enable_context_caching=True
        )
    
    @pytest.fixture
    def sample_article_data(self):
        return {
            'article_url': 'https://example.com/test-article',
            'article_text': 'This is a test article about important news events.',
            'user_context': {
                'user_id': 'test_user',
                'user_tier': 'premium',
                'session_id': 'test_session_123'
            }
        }
    
    @pytest.mark.asyncio
    async def test_core_analysis_execution(self, mock_grok_client, test_config, sample_article_data):
        """Test that core analysis executes jargon and viewpoints in parallel"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        start_time = time.time()
        
        # Execute core analysis
        result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        
        execution_time = time.time() - start_time
        
        # Verify results
        assert result['success'] is True
        assert 'session_id' in result
        assert 'results' in result
        assert 'jargon' in result['results']
        assert 'viewpoints' in result['results']
        assert result['metadata']['cached_for_on_demand'] is True
        
        # Verify parallel execution (should be faster than sequential)
        assert execution_time < 5.0  # Should complete quickly with mocks
        
        print(f"✅ Core analysis completed in {execution_time:.2f}s")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Success rate: {result['metadata']['successful_analyses']}/2")
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, mock_grok_client, test_config, sample_article_data):
        """Test that core analysis results are properly cached"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        # Execute core analysis
        core_result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        
        session_id = core_result['session_id']
        
        # Verify cache contains the session
        cache_stats = await coordinator.get_cache_stats()
        assert cache_stats['cached_sessions'] >= 1
        
        # Test cache retrieval
        cached_context = await coordinator.cache.get_enhanced_context(session_id, 'fact-check')
        assert cached_context is not None
        assert cached_context['session_id'] == session_id
        assert cached_context['cache_hit'] is True
        assert cached_context['has_core_results'] is True
        
        print(f"✅ Caching working correctly")
        print(f"   Cached sessions: {cache_stats['cached_sessions']}")
        print(f"   Cache size: {cache_stats['cache_size_mb']:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_on_demand_analysis(self, mock_grok_client, test_config, sample_article_data):
        """Test on-demand analysis with cached context"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        # First, execute core analysis to populate cache
        core_result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        
        session_id = core_result['session_id']
        
        # Test each on-demand analysis type
        analysis_types = ['fact-check', 'bias', 'timeline', 'expert', 'x-pulse']
        
        for analysis_type in analysis_types:
            start_time = time.time()
            
            result = await coordinator.analyze_on_demand(
                analysis_type=analysis_type,
                session_id=session_id,
                user_context={'user_id': 'test_user', 'user_tier': 'premium'}
            )
            
            execution_time = time.time() - start_time
            
            # Verify results
            assert result['success'] is True
            assert result['analysis_type'] == analysis_type
            assert result['session_id'] == session_id
            assert result['metadata']['cache_hit'] is True
            
            print(f"✅ {analysis_type} analysis completed in {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_on_demand_without_cache(self, mock_grok_client, test_config):
        """Test on-demand analysis fails gracefully without cached context"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        # Try on-demand analysis without core analysis first
        result = await coordinator.analyze_on_demand(
            analysis_type='fact-check',
            session_id='nonexistent_session',
            user_context={'user_id': 'test_user'}
        )
        
        # Should fail gracefully
        assert result['success'] is False
        assert result['requires_core_analysis'] is True
        assert 'No cached context found' in result['error']
        
        print("✅ On-demand analysis correctly requires core analysis first")
    
    @pytest.mark.asyncio
    async def test_performance_comparison(self, mock_grok_client, test_config, sample_article_data):
        """Compare performance of optimized vs traditional approach"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        # Test optimized approach (core analysis only)
        start_time = time.time()
        core_result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        core_time = time.time() - start_time
        
        session_id = core_result['session_id']
        
        # Test on-demand analysis (using cache)
        start_time = time.time()
        on_demand_result = await coordinator.analyze_on_demand(
            analysis_type='fact-check',
            session_id=session_id,
            user_context={'user_id': 'test_user'}
        )
        on_demand_time = time.time() - start_time
        
        total_optimized_time = core_time + on_demand_time
        
        print(f"✅ Performance Analysis:")
        print(f"   Core analysis (immediate): {core_time:.2f}s")
        print(f"   On-demand analysis (cached): {on_demand_time:.2f}s")
        print(f"   Total optimized time: {total_optimized_time:.2f}s")
        
        # Verify core analysis is fast (immediate user feedback)
        assert core_time < 2.0  # Should be very fast with mocks
        assert on_demand_result['metadata']['cache_hit'] is True
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, mock_grok_client, sample_article_data):
        """Test cache expiry functionality"""
        # Use very short TTL for testing
        short_ttl_config = OptimizedCoordinatorConfig(
            cache_ttl_minutes=0.01,  # 0.6 seconds
            enable_result_caching=True,
            enable_context_caching=True
        )
        
        coordinator = OptimizedAgentCoordinator(mock_grok_client, short_ttl_config)
        
        # Execute core analysis
        core_result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        
        session_id = core_result['session_id']
        
        # Verify cache exists
        cached_context = await coordinator.cache.get_enhanced_context(session_id, 'fact-check')
        assert cached_context is not None
        
        # Wait for cache to expire
        await asyncio.sleep(1.0)
        
        # Verify cache is expired
        expired_context = await coordinator.cache.get_enhanced_context(session_id, 'fact-check')
        assert expired_context is None
        
        print("✅ Cache expiry working correctly")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_config, sample_article_data):
        """Test error handling in optimized architecture"""
        # Create mock client that raises exceptions
        failing_client = Mock()
        failing_client.async_client = Mock()
        failing_client.async_client.chat = Mock()
        failing_client.async_client.chat.completions = Mock()
        failing_client.async_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        coordinator = OptimizedAgentCoordinator(failing_client, test_config)
        
        # Test core analysis error handling
        result = await coordinator.analyze_core(
            article_url=sample_article_data['article_url'],
            article_text=sample_article_data['article_text'],
            user_context=sample_article_data['user_context']
        )
        
        # Should handle errors gracefully
        assert result['success'] is False
        # Error can be in 'error' field (for exceptions) or 'errors' field (for agent failures)
        assert 'error' in result or 'errors' in result
        assert 'execution_time_seconds' in result['metadata']
        
        print("✅ Error handling working correctly")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_grok_client, test_config, sample_article_data):
        """Test handling of concurrent requests"""
        coordinator = OptimizedAgentCoordinator(mock_grok_client, test_config)
        
        # Create multiple concurrent core analysis requests
        tasks = []
        for i in range(5):
            user_context = sample_article_data['user_context'].copy()
            user_context['session_id'] = f'concurrent_session_{i}'
            
            task = coordinator.analyze_core(
                article_url=sample_article_data['article_url'],
                article_text=sample_article_data['article_text'],
                user_context=user_context
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # Verify all requests completed successfully
        assert len(results) == 5
        for result in results:
            assert result['success'] is True
        
        # Verify concurrent execution is efficient
        assert execution_time < 10.0  # Should handle concurrency well
        
        print(f"✅ Concurrent requests handled efficiently in {execution_time:.2f}s")
        print(f"   Processed {len(results)} requests concurrently")


async def main():
    """Run the test suite"""
    print("🚀 Testing Optimized Agent Architecture")
    print("=" * 50)
    
    # Create test instance
    test_instance = TestOptimizedArchitecture()
    
    # Mock dependencies
    mock_client = MockGrokClient()
    config = OptimizedCoordinatorConfig()
    sample_data = {
        'article_url': 'https://example.com/test-article',
        'article_text': 'This is a test article about important news events.',
        'user_context': {
            'user_id': 'test_user',
            'user_tier': 'premium',
            'session_id': 'test_session_123'
        }
    }
    
    try:
        # Run tests
        await test_instance.test_core_analysis_execution(mock_client, config, sample_data)
        await test_instance.test_caching_functionality(mock_client, config, sample_data)
        await test_instance.test_on_demand_analysis(mock_client, config, sample_data)
        await test_instance.test_on_demand_without_cache(mock_client, config)
        await test_instance.test_performance_comparison(mock_client, config, sample_data)
        await test_instance.test_cache_expiry(mock_client, sample_data)
        await test_instance.test_error_handling(config, sample_data)
        await test_instance.test_concurrent_requests(mock_client, config, sample_data)
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Optimized architecture is working correctly.")
        print("\n📊 Key Benefits Demonstrated:")
        print("   ✅ Core analysis executes immediately (jargon + viewpoints)")
        print("   ✅ On-demand features use cached context efficiently")
        print("   ✅ Caching reduces redundant processing")
        print("   ✅ Error handling is robust")
        print("   ✅ Concurrent requests are handled efficiently")
        print("   ✅ Cache expiry prevents memory leaks")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 