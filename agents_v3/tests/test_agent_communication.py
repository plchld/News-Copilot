#!/usr/bin/env python3
"""
Tests for inter-agent communication system
"""

import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.communication.agent_message_bus import AgentMessageBus, AgentMessage, MessageType, MessagePriority
from agents_v3.providers.base_agent import BaseAgent, AgentConfig, AgentRole, AgentResponse


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.responses = {}
        self.received_messages = []
    
    def _init_client(self):
        """Mock client initialization"""
        self.client = MagicMock()
    
    async def start_conversation(self, conversation_type: str = "analysis") -> str:
        """Mock conversation start"""
        return f"mock_conversation_{conversation_type}"
    
    async def send_message(
        self,
        conversation_id: str,
        message: str,
        story_context=None,
        cache_message: bool = True
    ) -> AgentResponse:
        """Mock message sending"""
        # Return pre-configured response or default
        content = self.responses.get(conversation_id, f"Mock analysis response for: {message[:50]}...")
        
        return AgentResponse(
            content=content,
            provider="mock",
            model="mock-model",
            conversation_id=conversation_id,
            tokens_used={"input": 100, "output": 50},
            cost_estimate=0.01
        )
    
    async def process_story_batch(
        self,
        conversation_id: str,
        stories
    ):
        """Mock batch processing"""
        results = []
        for story in stories:
            response = await self.send_message(conversation_id, f"Analyze: {story.get('headline', 'Unknown')}")
            results.append(response)
        return results
    
    async def end_conversation(self, conversation_id: str):
        """Mock conversation end"""
        return {
            "conversation_id": conversation_id,
            "total_cost": 0.05,
            "messages": 3,
            "cache_hit_ratio": 0.8
        }
    
    async def _search_web_impl(self, query: str, **kwargs):
        """Mock web search"""
        return [{"title": f"Mock result for {query}", "url": "http://mock.com", "content": "Mock content"}]
    
    def set_response(self, conversation_id: str, response: str):
        """Set a specific response for testing"""
        self.responses[conversation_id] = response
    
    async def mock_message_handler(self, message: AgentMessage):
        """Mock message handler"""
        self.received_messages.append(message)
        
        if message.requires_response:
            return {"mock_response": f"Handled {message.subject}"}
        return None


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def message_bus():
    """Create and start message bus for testing"""
    bus = AgentMessageBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def sample_agents():
    """Create sample agents for testing"""
    discovery_config = AgentConfig(
        name="discovery_agent",
        role=AgentRole.DISCOVERY,
        instructions="Mock discovery agent",
        provider="mock"
    )
    
    greek_config = AgentConfig(
        name="greek_perspective_agent",
        role=AgentRole.PERSPECTIVE,
        instructions="Mock Greek perspective agent",
        provider="mock"
    )
    
    synthesis_config = AgentConfig(
        name="synthesis_agent",
        role=AgentRole.SYNTHESIS,
        instructions="Mock synthesis agent",
        provider="mock"
    )
    
    return {
        "discovery": MockAgent(discovery_config),
        "greek": MockAgent(greek_config),
        "synthesis": MockAgent(synthesis_config)
    }


@pytest.fixture
def sample_story():
    """Sample story data for testing"""
    return {
        "id": "test_story_123",
        "headline": "Test News Story",
        "category": "politics",
        "why_important": "This is a test story for validation",
        "key_facts": [
            "Fact 1: Something happened",
            "Fact 2: Someone said something",
            "Fact 3: There are implications"
        ],
        "source": "test_source.com"
    }


class TestAgentMessageBus:
    """Test the agent message bus functionality"""
    
    async def test_bus_lifecycle(self, message_bus):
        """Test message bus start/stop lifecycle"""
        assert message_bus.running
        
        await message_bus.stop()
        assert not message_bus.running
    
    async def test_agent_registration(self, message_bus, sample_agents):
        """Test agent registration and unregistration"""
        agent = sample_agents["discovery"]
        
        # Register agent
        message_bus.register_agent(agent.agent_id, agent)
        assert agent.agent_id in message_bus.agents
        assert agent.agent_id in message_bus.message_queues
        
        # Unregister agent
        message_bus.unregister_agent(agent.agent_id)
        assert agent.agent_id not in message_bus.agents
        assert agent.agent_id not in message_bus.message_queues
    
    async def test_direct_message_sending(self, message_bus, sample_agents):
        """Test direct message sending between agents"""
        sender = sample_agents["discovery"]
        receiver = sample_agents["greek"]
        
        # Register agents
        message_bus.register_agent(sender.agent_id, sender)
        message_bus.register_agent(receiver.agent_id, receiver)
        
        # Register message handler
        message_bus.register_message_handler(
            receiver.agent_id,
            MessageType.REQUEST,
            receiver.mock_message_handler
        )
        
        # Create and send message
        message = AgentMessage(
            id="test_msg_123",
            sender_id=sender.agent_id,
            receiver_id=receiver.agent_id,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            subject="Test Analysis Request",
            content={"test": "data"}
        )
        
        await message_bus.send_message(message)
        
        # Wait a bit for message processing
        await asyncio.sleep(0.2)
        
        # Check that receiver got the message
        assert len(receiver.received_messages) == 1
        assert receiver.received_messages[0].id == "test_msg_123"
    
    async def test_request_response_pattern(self, message_bus, sample_agents):
        """Test request-response message pattern"""
        requester = sample_agents["discovery"]
        responder = sample_agents["synthesis"]
        
        # Register agents
        message_bus.register_agent(requester.agent_id, requester)
        message_bus.register_agent(responder.agent_id, responder)
        
        # Register response handler
        message_bus.register_message_handler(
            responder.agent_id,
            MessageType.REQUEST,
            responder.mock_message_handler
        )
        
        # Send request expecting response
        message = AgentMessage(
            id="test_req_123",
            sender_id=requester.agent_id,
            receiver_id=responder.agent_id,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            subject="Test Request",
            content={"analysis_type": "test"},
            requires_response=True,
            response_timeout_seconds=5
        )
        
        response = await message_bus.send_message(message)
        
        # Should receive response
        assert response is not None
        assert response.message_type == MessageType.RESPONSE
        assert "mock_response" in response.content
    
    async def test_broadcast_message(self, message_bus, sample_agents):
        """Test broadcast message to all agents"""
        agents = list(sample_agents.values())
        
        # Register all agents
        for agent in agents:
            message_bus.register_agent(agent.agent_id, agent)
            message_bus.register_message_handler(
                agent.agent_id,
                MessageType.BROADCAST,
                agent.mock_message_handler
            )
        
        # Send broadcast message
        broadcast_msg = AgentMessage(
            id="broadcast_123",
            sender_id=agents[0].agent_id,
            receiver_id=None,  # None = broadcast
            message_type=MessageType.BROADCAST,
            priority=MessagePriority.HIGH,
            subject="System Announcement",
            content={"announcement": "System update"}
        )
        
        await message_bus.send_message(broadcast_msg)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # All agents except sender should receive message
        for i, agent in enumerate(agents):
            if i == 0:  # Sender shouldn't receive own broadcast
                assert len(agent.received_messages) == 0
            else:
                assert len(agent.received_messages) == 1
                assert agent.received_messages[0].subject == "System Announcement"


class TestInterAgentCommunication:
    """Test inter-agent communication features"""
    
    async def test_agent_analysis_request(self, message_bus, sample_agents, sample_story):
        """Test agent requesting analysis from another agent"""
        requester = sample_agents["discovery"]
        analyst = sample_agents["greek"]
        
        # Set up agents with message bus
        requester.set_message_bus(message_bus)
        analyst.set_message_bus(message_bus)
        
        # Register request handler for analyst
        analyst.register_message_handler(
            MessageType.REQUEST,
            analyst.handle_analysis_request
        )
        
        # Set up analyst response
        analyst.set_response("mock_conversation_inter_agent_perspective", "Detailed Greek perspective analysis of the test story")
        
        # Request analysis
        result = await requester.request_analysis_from_agent(
            target_agent_id=analyst.agent_id,
            analysis_type="perspective",
            story_data=sample_story,
            timeout_seconds=10
        )
        
        # Check result
        assert result is not None
        assert "analysis_type" in result
        assert result["analysis_type"] == "perspective"
        assert "result" in result
        assert "Greek perspective" in result["result"]
    
    async def test_synthesis_request(self, message_bus, sample_agents, sample_story):
        """Test synthesis request with multiple perspectives"""
        requester = sample_agents["discovery"]
        synthesizer = sample_agents["synthesis"]
        
        # Set up agents
        requester.set_message_bus(message_bus)
        synthesizer.set_message_bus(message_bus)
        
        # Register synthesis handler
        synthesizer.register_message_handler(
            MessageType.REQUEST,
            synthesizer.handle_analysis_request
        )
        
        # Set up synthesis response
        synthesizer.set_response(
            "mock_conversation_inter_agent_synthesis",
            "Comprehensive synthesis integrating Greek and international perspectives"
        )
        
        # Create mock perspectives
        perspectives = {
            "greek_perspective": {
                "result": "Greek media emphasizes national sovereignty concerns",
                "provider": "anthropic",
                "cost": 0.02
            },
            "international_perspective": {
                "result": "International coverage focuses on EU implications",
                "provider": "anthropic",
                "cost": 0.02
            }
        }
        
        # Request synthesis
        result = await requester.request_synthesis(
            synthesis_agent_id=synthesizer.agent_id,
            story_data=sample_story,
            perspectives=perspectives
        )
        
        # Check result
        assert result is not None
        assert "analysis_type" in result
        assert result["analysis_type"] == "synthesis"
        assert "Comprehensive synthesis" in result["result"]
    
    async def test_collaboration_session(self, message_bus, sample_agents, sample_story):
        """Test multi-agent collaboration session"""
        initiator = sample_agents["discovery"]
        participants = [sample_agents["greek"], sample_agents["synthesis"]]
        
        # Set up all agents
        initiator.set_message_bus(message_bus)
        for participant in participants:
            participant.set_message_bus(message_bus)
            participant.register_message_handler(
                MessageType.COLLABORATION,
                participant.mock_message_handler
            )
        
        # Start collaboration
        collaboration_id = await initiator.collaborate_on_story(
            participant_agent_ids=[p.agent_id for p in participants],
            collaboration_type="multi_perspective_analysis",
            story_data=sample_story
        )
        
        # Wait for collaboration messages
        await asyncio.sleep(0.2)
        
        # Check that collaboration was set up
        assert collaboration_id in message_bus.collaboration_sessions
        
        session = message_bus.collaboration_sessions[collaboration_id]
        assert session["initiator"] == initiator.agent_id
        assert session["type"] == "multi_perspective_analysis"
        
        # Check that participants received collaboration invitations
        for participant in participants:
            assert len(participant.received_messages) == 1
            msg = participant.received_messages[0]
            assert msg.message_type == MessageType.COLLABORATION
            assert msg.content["collaboration_id"] == collaboration_id


class TestAgentMessageSystem:
    """Test the overall agent message system"""
    
    async def test_message_history_tracking(self, message_bus, sample_agents):
        """Test message history tracking and retrieval"""
        sender = sample_agents["discovery"]
        receiver = sample_agents["greek"]
        
        # Register agents
        message_bus.register_agent(sender.agent_id, sender)
        message_bus.register_agent(receiver.agent_id, receiver)
        
        # Send multiple messages
        for i in range(3):
            message = AgentMessage(
                id=f"msg_{i}",
                sender_id=sender.agent_id,
                receiver_id=receiver.agent_id,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.MEDIUM,
                subject=f"Message {i}",
                content={"index": i}
            )
            await message_bus.send_message(message)
        
        # Check message history
        history = message_bus.get_message_history()
        assert len(history) == 3
        
        # Filter by agent
        sender_history = message_bus.get_message_history(agent_id=sender.agent_id)
        assert len(sender_history) == 3
        
        # Filter by message type
        request_history = message_bus.get_message_history(message_type=MessageType.REQUEST)
        assert len(request_history) == 3
    
    async def test_error_handling(self, message_bus, sample_agents):
        """Test error handling in message system"""
        sender = sample_agents["discovery"]
        
        # Register sender
        message_bus.register_agent(sender.agent_id, sender)
        
        # Try to send message to non-existent agent
        message = AgentMessage(
            id="error_test",
            sender_id=sender.agent_id,
            receiver_id="non_existent_agent",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.MEDIUM,
            subject="Error Test",
            content={"test": "error"}
        )
        
        # Should not raise exception
        await message_bus.send_message(message)
        
        # Message should still be in history
        history = message_bus.get_message_history()
        assert len(history) == 1
        assert history[0].id == "error_test"


if __name__ == "__main__":
    # Run specific test
    async def run_test():
        """Run a simple test without pytest"""
        print("🧪 Testing Agent Communication System")
        print("=" * 50)
        
        # Create message bus
        bus = AgentMessageBus()
        await bus.start()
        
        try:
            # Create test agents
            config1 = AgentConfig(
                name="test_agent_1",
                role=AgentRole.DISCOVERY,
                instructions="Test agent 1",
                provider="mock"
            )
            
            config2 = AgentConfig(
                name="test_agent_2", 
                role=AgentRole.PERSPECTIVE,
                instructions="Test agent 2",
                provider="mock"
            )
            
            agent1 = MockAgent(config1)
            agent2 = MockAgent(config2)
            
            # Set up message bus
            agent1.set_message_bus(bus)
            agent2.set_message_bus(bus)
            
            # Register handlers
            agent2.register_message_handler(MessageType.REQUEST, agent2.handle_analysis_request)
            
            # Test analysis request
            story = {
                "id": "test_123",
                "headline": "Test Story",
                "category": "test",
                "why_important": "Testing purposes",
                "key_facts": ["Test fact 1", "Test fact 2"]
            }
            
            print("📤 Requesting analysis...")
            result = await agent1.request_analysis_from_agent(
                target_agent_id=agent2.agent_id,
                analysis_type="test_analysis",
                story_data=story
            )
            
            print("📥 Received result:")
            print(f"   Analysis Type: {result.get('analysis_type')}")
            print(f"   Result: {result.get('result', '')[:100]}...")
            print(f"   Provider: {result.get('provider')}")
            print(f"   Cost: ${result.get('cost_estimate', 0):.4f}")
            
            print("\n✅ Communication test completed successfully!")
            
        finally:
            await bus.stop()
    
    # Run the test
    asyncio.run(run_test())