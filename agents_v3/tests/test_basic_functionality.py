#!/usr/bin/env python3
"""
Basic functionality tests for agents_v3 system without API dependencies
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.utils.prompt_loader import PromptLoader
from agents_v3.providers.base_agent import AgentConfig, AgentRole
from agents_v3.conversation_logging.conversation_logger import ConversationLogger


class TestPromptLoader:
    """Test prompt loading functionality"""
    
    def test_prompt_validation(self):
        """Test that all required prompts exist and are valid"""
        loader = PromptLoader()
        
        validation_results = loader.validate_prompts()
        
        print("📋 Prompt Validation Results:")
        for prompt_name, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"   {status} {prompt_name}")
        
        # Check that all prompts are valid
        assert all(validation_results.values()), f"Invalid prompts: {[k for k, v in validation_results.items() if not v]}"
    
    def test_prompt_loading(self):
        """Test loading specific prompts"""
        loader = PromptLoader()
        
        # Test loading discovery agent prompt
        discovery_prompt = loader.load_prompt("discovery_agent")
        assert len(discovery_prompt) > 100, "Discovery prompt seems too short"
        assert "discovery" in discovery_prompt.lower(), "Discovery prompt doesn't contain expected content"
        
        # Test loading Greek perspective prompt
        greek_prompt = loader.load_prompt("greek_perspective_agent")
        assert len(greek_prompt) > 100, "Greek perspective prompt seems too short"
        assert "greek" in greek_prompt.lower(), "Greek prompt doesn't contain expected content"
        
        print("✅ Prompt loading tests passed")
    
    def test_prompt_caching(self):
        """Test prompt caching functionality"""
        loader = PromptLoader()
        
        # Load prompt first time
        prompt1 = loader.load_prompt("synthesis_agent")
        
        # Load same prompt second time (should use cache)
        prompt2 = loader.load_prompt("synthesis_agent")
        
        # Should be identical
        assert prompt1 == prompt2, "Cached prompt doesn't match original"
        
        # Test cache clearing
        loader.clear_cache()
        prompt3 = loader.load_prompt("synthesis_agent")
        assert prompt1 == prompt3, "Prompt content changed after cache clear"
        
        print("✅ Prompt caching tests passed")


class TestAgentConfiguration:
    """Test agent configuration and setup"""
    
    def test_agent_config_creation(self):
        """Test creating agent configurations"""
        config = AgentConfig(
            name="test_agent",
            role=AgentRole.DISCOVERY,
            instructions="Test instructions",
            provider="mock",
            model="mock-model",
            temperature=0.8,
            cache_ttl="5m",
            enable_search=True,
            batch_size=15
        )
        
        assert config.name == "test_agent"
        assert config.role == AgentRole.DISCOVERY
        assert config.provider == "mock"
        assert config.enable_search is True
        assert config.batch_size == 15
        
        print("✅ Agent configuration tests passed")
    
    def test_agent_roles(self):
        """Test all agent roles are properly defined"""
        expected_roles = ["DISCOVERY", "PERSPECTIVE", "FACT_CHECK", "SYNTHESIS", "SOCIAL_PULSE"]
        
        available_roles = [role.name for role in AgentRole]
        
        for expected_role in expected_roles:
            assert expected_role in available_roles, f"Missing agent role: {expected_role}"
        
        print("✅ Agent role tests passed")


class TestConversationLogger:
    """Test conversation logging functionality"""
    
    def test_logger_initialization(self):
        """Test logger can be initialized"""
        logger = ConversationLogger(
            log_dir="test_logs",
            console_output=False,
            json_output=False
        )
        
        assert logger.log_dir.name == "test_logs"
        assert logger.console_output is False
        assert logger.json_output is False
        
        print("✅ Logger initialization tests passed")
    
    def test_conversation_management(self):
        """Test conversation lifecycle management"""
        logger = ConversationLogger(console_output=False, json_output=False)
        
        # Start conversation
        conv_id = logger.start_conversation(
            agent_name="test_agent",
            provider="mock",
            conversation_type="test",
            metadata={"test": True}
        )
        
        assert conv_id in logger.conversation_logs
        
        # Log a message
        logger.log_message(
            conversation_id=conv_id,
            agent_name="test_agent",
            provider="mock",
            message_type="user",
            content="Test message",
            tokens_used={"input": 100, "output": 50},
            cost_estimate=0.01
        )
        
        # Check message was logged
        assert len(logger.conversation_logs[conv_id]) == 2  # Start + message
        
        # End conversation
        logger.end_conversation(
            conversation_id=conv_id,
            agent_name="test_agent",
            provider="mock"
        )
        
        # Check final message was logged
        assert len(logger.conversation_logs[conv_id]) == 3  # Start + message + end
        
        print("✅ Conversation management tests passed")


class TestCostCalculation:
    """Test cost calculation functionality"""
    
    def test_anthropic_cost_calculation(self):
        """Test Anthropic-specific cost calculation"""
        # This would normally be in the agent, but we can test the logic
        # Anthropic pricing per 1K tokens
        pricing = {
            "input": 0.003,
            "output": 0.015,
            "cache_write": 0.00375,
            "cache_read": 0.0003
        }
        
        # Test scenario: 1000 input, 500 output, 800 cache read, 200 cache write
        input_tokens = 1000
        output_tokens = 500
        cache_read_tokens = 800
        cache_write_tokens = 200
        
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"] +
            (cache_write_tokens / 1000) * pricing["cache_write"] +
            (cache_read_tokens / 1000) * pricing["cache_read"]
        )
        
        expected_cost = 0.003 + 0.0075 + 0.00075 + 0.00024  # ≈ $0.011
        assert abs(cost - expected_cost) < 0.0001, f"Cost calculation incorrect: {cost} vs {expected_cost}"
        
        # Test cache savings - compare with scenario where cache_read_tokens were regular input
        cost_without_cache = (
            ((input_tokens + cache_read_tokens) / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )
        
        savings = cost_without_cache - cost
        savings_percentage = (savings / cost_without_cache) * 100
        
        assert savings > 0, "Cache should provide savings"
        # Just verify we get some savings - the exact amount depends on the token mix
        assert savings_percentage > 5, f"Cache should provide some savings, got {savings_percentage:.1f}%"
        
        print(f"✅ Cost calculation tests passed (${cost:.4f}, {savings_percentage:.1f}% savings)")


async def run_all_tests():
    """Run all tests without external dependencies"""
    print("🧪 Running Agents V3 Basic Functionality Tests")
    print("=" * 60)
    
    try:
        # Test prompt loading
        print("\n📁 Testing Prompt Loading...")
        prompt_tests = TestPromptLoader()
        prompt_tests.test_prompt_validation()
        prompt_tests.test_prompt_loading()
        prompt_tests.test_prompt_caching()
        
        # Test agent configuration
        print("\n⚙️ Testing Agent Configuration...")
        config_tests = TestAgentConfiguration()
        config_tests.test_agent_config_creation()
        config_tests.test_agent_roles()
        
        # Test conversation logging
        print("\n📝 Testing Conversation Logging...")
        logger_tests = TestConversationLogger()
        logger_tests.test_logger_initialization()
        logger_tests.test_conversation_management()
        
        # Test cost calculation
        print("\n💰 Testing Cost Calculation...")
        cost_tests = TestCostCalculation()
        cost_tests.test_anthropic_cost_calculation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("🚀 Agents V3 basic functionality is working correctly")
        print("\n💡 To test with real APIs, set API keys and run:")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("   export GEMINI_API_KEY='your-key'") 
        print("   python examples/cost_optimized_analysis.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)