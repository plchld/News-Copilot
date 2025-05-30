"""Test runner for agents_v2"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import our modules
from test_agents_with_mocks import main as test_basic
from test_with_tracing import main as test_tracing


async def run_all_tests():
    """Run all test suites"""
    print("🧪 Running News Copilot Agents v2 Test Suite")
    print("=" * 50)
    
    try:
        print("\n📋 Test 1: Basic Agent Functionality")
        await test_basic()
        
        print("\n📋 Test 2: Advanced Tracing")
        await test_tracing()
        
        print("\n🎉 All test suites passed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())