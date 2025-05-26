"""
Test suite for async communication patterns in the agent system.
Verifies proper async usage, error handling, and sub-agent communication.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentResult, AgentConfig, ModelType, ComplexityLevel, AsyncCommunicationMixin
from .optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType
from .x_pulse_agent import XPulseAgent
from .collaborative_agents import MessageBus, AgentMessage


class MockGrokClient:
    """Mock Grok client for testing"""
    
    def __init__(self):
        self.async_client = Mock()
        self.async_client.chat = Mock()
        self.async_client.chat.completions = Mock()
        self.async_client.chat.completions.create = AsyncMock()
        
    async def mock_response(self, delay: float = 0.1):
        """Mock async response with configurable delay"""
        await asyncio.sleep(delay)
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"test": "response"}'
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 100
        return mock_response


class TestAsyncCommunicationMixin:
    """Test the async communication utilities"""
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        """Test successful execution with timeout"""
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await AsyncCommunicationMixin.execute_with_timeout(
            quick_task(), timeout_seconds=1, agent_name="test"
        )
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_failure(self):
        """Test timeout handling"""
        async def slow_task():
            await asyncio.sleep(2)
            return "success"
        
        with pytest.raises(Exception, match="timed out after 0.5 seconds"):
            await AsyncCommunicationMixin.execute_with_timeout(
                slow_task(), timeout_seconds=0.5, agent_name="test"
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_semaphore(self):
        """Test semaphore-controlled execution"""
        semaphore = asyncio.Semaphore(2)
        results = []
        
        async def task(task_id: int):
            async with semaphore:
                await asyncio.sleep(0.1)
                results.append(task_id)
                return task_id
        
        # Execute 4 tasks with semaphore limit of 2
        tasks = [
            AsyncCommunicationMixin.execute_with_semaphore(semaphore, task(i), f"task_{i}")
            for i in range(4)
        ]
        
        await asyncio.gather(*tasks)
        assert len(results) == 4
        assert set(results) == {0, 1, 2, 3}
    
    @pytest.mark.asyncio
    async def test_gather_with_error_handling(self):
        """Test enhanced gather with error handling"""
        async def success_task():
            return "success"
        
        async def failure_task():
            raise ValueError("test error")
        
        results = await AsyncCommunicationMixin.gather_with_error_handling(
            success_task(), failure_task()
        )
        
        assert len(results) == 2
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test retry mechanism with eventual success"""
        attempt_count = 0
        
        def task_factory():
            async def task():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 3:
                    raise ValueError("temporary failure")
                return "success"
            return task()
        
        result = await AsyncCommunicationMixin.execute_with_retry(
            task_factory, max_retries=3, backoff_factor=0.1, agent_name="test"
        )
        
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self):
        """Test retry mechanism with persistent failure"""
        def task_factory():
            async def task():
                raise ValueError("persistent failure")
            return task()
        
        with pytest.raises(Exception, match="failed after 2 attempts"):
            await AsyncCommunicationMixin.execute_with_retry(
                task_factory, max_retries=2, backoff_factor=0.1, agent_name="test"
            )


class TestMessageBus:
    """Test the async message bus"""
    
    @pytest.mark.asyncio
    async def test_message_publishing_and_retrieval(self):
        """Test basic message publishing and retrieval"""
        bus = MessageBus()
        
        # Subscribe agent to message types
        bus.subscribe("agent1", ["type1", "type2"])
        bus.subscribe("agent2", ["type2"])
        
        # Publish messages
        await bus.publish(AgentMessage(
            from_agent="sender",
            to_agent=None,
            message_type="type1",
            content="broadcast message"
        ))
        
        await bus.send_direct_message(
            to_agent="agent1",
            message_type="direct",
            content="direct message",
            from_agent="sender"
        )
        
        # Retrieve messages
        agent1_messages = await bus.get_messages_for_agent("agent1", timeout=0.1)
        agent2_messages = await bus.get_messages_for_agent("agent2", timeout=0.1)
        
        assert len(agent1_messages) == 2  # broadcast + direct
        assert len(agent2_messages) == 0  # no type1 subscription
        
        # Check message content
        broadcast_msg = next(msg for msg in agent1_messages if msg.message_type == "type1")
        direct_msg = next(msg for msg in agent1_messages if msg.message_type == "direct")
        
        assert broadcast_msg.content == "broadcast message"
        assert direct_msg.content == "direct message"
        assert direct_msg.to_agent == "agent1"
    
    @pytest.mark.asyncio
    async def test_message_bus_shutdown(self):
        """Test graceful shutdown of message bus"""
        bus = MessageBus()
        
        # Add some messages
        await bus.publish(AgentMessage(
            from_agent="test",
            to_agent=None,
            message_type="test",
            content="test"
        ))
        
        # Shutdown should clear queue
        await bus.shutdown()
        
        # Queue should be empty after shutdown
        messages = await bus.get_messages_for_agent("any_agent", timeout=0.1)
        assert len(messages) == 0


class TestCoordinatorAsyncPatterns:
    """Test coordinator async patterns"""
    
    @pytest.mark.asyncio
    async def test_parallel_execution_with_semaphore(self):
        """Test that coordinator properly uses semaphore for concurrency control"""
        mock_client = MockGrokClient()
        
        # Mock the agent execution to track concurrency
        execution_times = []
        max_concurrent = 0
        current_concurrent = 0
        
        async def mock_execute(context):
            nonlocal current_concurrent, max_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            
            start_time = datetime.now()
            await asyncio.sleep(0.1)  # Simulate work
            end_time = datetime.now()
            
            execution_times.append((start_time, end_time))
            current_concurrent -= 1
            
            return AgentResult(
                success=True,
                data={"test": "data"},
                execution_time_ms=100,
                agent_name="test_agent"
            )
        
        # Create coordinator with limited concurrency
        coordinator = AgentCoordinator(mock_client)
        coordinator.config.max_parallel_agents = 2
        
        # Mock all agents to use our mock execute
        for agent in coordinator.agents.values():
            agent.execute = mock_execute
        
        # Execute multiple agents
        analysis_types = [
            AnalysisType.JARGON,
            AnalysisType.VIEWPOINTS,
            AnalysisType.FACT_CHECK,
            AnalysisType.BIAS
        ]
        
        results = await coordinator._execute_parallel(
            analysis_types,
            {"article_text": "test", "session_id": "test"}
        )
        
        # Verify results
        assert len(results) == 4
        assert all(result.success for result in results.values())
        
        # Verify concurrency was limited (should never exceed 2)
        assert max_concurrent <= 2
        assert len(execution_times) == 4


class TestXPulseAgentOrchestration:
    """Test XPulse agent sub-agent orchestration"""
    
    @pytest.mark.asyncio
    async def test_sub_agent_error_handling(self):
        """Test that XPulse agent handles sub-agent failures gracefully"""
        mock_client = MockGrokClient()
        
        # Create XPulse agent
        x_pulse = XPulseAgent.create(mock_client)
        
        # Mock sub-agents with different behaviors
        x_pulse.sub_agents[0].execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"x_search_keywords": ["test", "keyword"]},
            agent_name="KeywordExtractorAgent"
        ))
        
        x_pulse.sub_agents[1].execute = AsyncMock(return_value=AgentResult(
            success=False,
            error="Search failed",
            data={"posts": []},
            agent_name="XSearchAgent"
        ))
        
        x_pulse.sub_agents[2].execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"themes": [{"theme_title": "test"}]},
            agent_name="ThemeAnalyzerAgent"
        ))
        
        x_pulse.sub_agents[3].execute = AsyncMock(side_effect=Exception("Sentiment analysis failed"))
        
        # Execute and verify graceful handling
        results = await x_pulse._execute_sub_agents({
            "article_text": "test",
            "session_id": "test"
        })
        
        assert len(results) == 4
        assert results[0].success  # Keywords succeeded
        assert not results[1].success  # Search failed but handled
        assert results[2].success  # Themes succeeded
        assert not results[3].success  # Sentiment failed but handled
        
        # Verify that execution continued despite failures
        assert "Sentiment analysis failed" in results[3].error


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 