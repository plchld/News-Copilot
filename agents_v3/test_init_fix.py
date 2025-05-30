#!/usr/bin/env python3
"""Test that the initialization fix works"""

import asyncio
import sys
from orchestration.category_orchestrator import CategoryOrchestrator

async def test_initialization():
    """Test that agents can be initialized without errors"""
    try:
        print("Creating orchestrator...")
        orchestrator = CategoryOrchestrator()
        
        print("Initializing agents...")
        await orchestrator.initialize_agents()
        
        print("✅ All agents initialized successfully!")
        print(f"   - Discovery agents: {len(orchestrator.discovery_agents)}")
        print(f"   - Context agents: {len(orchestrator.context_agents)}")
        print(f"   - Fact-check agent: {orchestrator.factcheck_agent is not None}")
        print(f"   - Synthesis agent: {orchestrator.synthesis_agent is not None}")
        
        # Clean up
        await orchestrator.message_bus.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_initialization())
    sys.exit(0 if success else 1)