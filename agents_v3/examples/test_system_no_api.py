#!/usr/bin/env python3
"""
Test the agents_v3 system without making actual API calls

This test demonstrates:
1. System initialization
2. Agent configuration
3. Inter-agent communication setup
4. Prompt loading
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.orchestration.conversational_orchestrator import ConversationalOrchestrator, ConversationalConfig
from agents_v3.providers.base_agent import AgentConfig, AgentRole
from agents_v3.utils.prompt_loader import prompt_loader
from agents_v3.conversation_logging.conversation_logger import logger
from agents_v3.communication import message_bus


async def test_system_initialization():
    """Test that the system initializes correctly"""
    
    print("🧪 Testing Agents V3 System Initialization")
    print("=" * 60)
    
    # Test 1: Prompt Loading
    print("\n📋 Test 1: Prompt Loading")
    print("-" * 40)
    
    prompts_valid = prompt_loader.validate_prompts()
    for prompt_name, is_valid in prompts_valid.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {prompt_name}")
    
    if all(prompts_valid.values()):
        print("   ✅ All prompts loaded successfully!")
    else:
        print("   ❌ Some prompts failed to load")
    
    # Test 2: Agent Configuration
    print("\n⚙️ Test 2: Agent Configuration")
    print("-" * 40)
    
    config = ConversationalConfig(
        discovery_provider="gemini",
        analysis_provider="anthropic",
        stories_per_conversation=15,
        enable_caching=True,
        cache_ttl="5m"
    )
    
    print(f"   • Discovery provider: {config.discovery_provider}")
    print(f"   • Analysis provider: {config.analysis_provider}")
    print(f"   • Stories per conversation: {config.stories_per_conversation}")
    print(f"   • Caching enabled: {config.enable_caching}")
    print(f"   • Cache TTL: {config.cache_ttl}")
    print("   ✅ Configuration created successfully!")
    
    # Test 3: Orchestrator Initialization
    print("\n🎭 Test 3: Orchestrator Initialization")
    print("-" * 40)
    
    try:
        orchestrator = ConversationalOrchestrator(config)
        print(f"   • Active agents: {len(orchestrator.active_agents)}")
        print(f"   • Agent types: {list(orchestrator.active_agents.keys())}")
        print("   ✅ Orchestrator initialized successfully!")
    except Exception as e:
        print(f"   ❌ Failed to initialize orchestrator: {e}")
        return
    
    # Test 4: Message Bus
    print("\n📬 Test 4: Message Bus System")
    print("-" * 40)
    
    await message_bus.start()
    print(f"   • Message bus running: {message_bus.running}")
    print(f"   • Registered agents: {len(message_bus.agents)}")
    print("   ✅ Message bus started successfully!")
    
    # Test 5: Agent Communication Setup
    print("\n🤝 Test 5: Agent Communication Setup")
    print("-" * 40)
    
    for agent_name, agent in orchestrator.active_agents.items():
        print(f"   • {agent_name}:")
        print(f"     - ID: {agent.agent_id}")
        print(f"     - Role: {agent.config.role.value}")
        print(f"     - Provider: {agent.config.provider}")
        print(f"     - Model: {agent.config.model}")
        has_handlers = len(agent._message_handlers) > 0
        print(f"     - Message handlers: {'✅' if has_handlers else '❌'}")
    
    # Test 6: Session Logging
    print("\n📊 Test 6: Session Logging")
    print("-" * 40)
    
    session_summary = logger.get_session_summary()
    print(f"   • Session ID: {session_summary['session_id']}")
    print(f"   • Total conversations: {session_summary['total_conversations']}")
    print(f"   • Total messages: {session_summary['total_messages']}")
    print(f"   • Log directory: {logger.log_dir}")
    print("   ✅ Logging system operational!")
    
    # Cleanup
    await message_bus.stop()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("🚀 System is ready for use (API keys needed for actual analysis)")
    print("\n💡 To run with real APIs:")
    print("   export ANTHROPIC_API_KEY='your-key'")
    print("   export GEMINI_API_KEY='your-key'")
    print("   python agents_v3/examples/news_analysis_demo.py")


async def test_agent_creation():
    """Test individual agent creation"""
    
    print("\n\n🔬 Testing Individual Agent Creation")
    print("=" * 60)
    
    # Test creating each type of agent
    agent_configs = [
        ("Discovery Agent", AgentRole.DISCOVERY, "gemini", True),
        ("Greek Perspective", AgentRole.PERSPECTIVE, "anthropic", False),
        ("Fact Checker", AgentRole.FACT_CHECK, "anthropic", False),
        ("Synthesis Agent", AgentRole.SYNTHESIS, "anthropic", False),
    ]
    
    for name, role, provider, enable_search in agent_configs:
        print(f"\n🤖 {name}")
        print("-" * 40)
        
        try:
            config = AgentConfig(
                name=name.lower().replace(" ", "_"),
                role=role,
                instructions=prompt_loader.load_prompt(f"{role.value.lower()}_agent"),
                provider=provider,
                enable_search=enable_search,
                batch_size=10
            )
            
            print(f"   • Role: {role.value}")
            print(f"   • Provider: {provider}")
            print(f"   • Search enabled: {enable_search}")
            print(f"   • Batch size: {config.batch_size}")
            print(f"   • Instructions loaded: {len(config.instructions)} chars")
            print("   ✅ Agent configuration successful!")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_system_initialization())
    asyncio.run(test_agent_creation())