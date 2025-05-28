#!/usr/bin/env python3
"""
Test API imports to identify issues
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_imports():
    """Test API-related imports"""
    print("Testing API imports...")
    
    try:
        from api.main_api import create_api_app
        print("✓ Main API imported")
    except Exception as e:
        print(f"✗ Main API error: {e}")
        return False
    
    try:
        from api.agent_api import agent_api
        print("✓ Agent API imported")
    except Exception as e:
        print(f"✗ Agent API error: {e}")
        return False
    
    try:
        from api.article_api import article_api
        print("✓ Article API imported")
    except Exception as e:
        print(f"✗ Article API error: {e}")
        return False
    
    # Test app creation
    try:
        app = create_api_app()
        print("✓ API app created successfully")
        return True
    except Exception as e:
        print(f"✗ API app creation error: {e}")
        return False

def test_agent_coordinator():
    """Test agent coordinator"""
    print("\nTesting agent coordinator...")
    
    try:
        from agents.news_agent_coordinator import NewsAgentCoordinator
        coordinator = NewsAgentCoordinator()
        print("✓ NewsAgentCoordinator created")
        
        agents = coordinator.get_available_agents()
        print(f"✓ Available agents: {agents}")
        
        agent_info = coordinator.get_agent_info()
        print(f"✓ Agent info loaded for {len(agent_info)} agents")
        
        return True
    except Exception as e:
        print(f"✗ Agent coordinator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("API IMPORTS TEST")
    print("=" * 50)
    
    api_ok = test_api_imports()
    agent_ok = test_agent_coordinator()
    
    print("\n" + "=" * 50)
    if api_ok and agent_ok:
        print("✅ ALL IMPORTS SUCCESSFUL")
        print("Ready to start the API server!")
    else:
        print("❌ IMPORT ISSUES FOUND")
        print("Need to fix import errors before starting server")

if __name__ == "__main__":
    main()