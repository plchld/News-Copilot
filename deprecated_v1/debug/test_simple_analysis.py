#!/usr/bin/env python3
"""
Simple test to debug the analysis issues
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_simple_analysis():
    """Test a simple analysis to see what's failing"""
    try:
        from api.grok_client import GrokClient
        from api.agents.optimized_coordinator import OptimizedAgentCoordinator, OptimizedCoordinatorConfig
        
        print("🔧 Setting up coordinator...")
        client = GrokClient()
        config = OptimizedCoordinatorConfig(
            core_timeout_seconds=30,  # Shorter timeout for testing
            on_demand_timeout_seconds=60
        )
        coordinator = OptimizedAgentCoordinator(client, config)
        
        print("🧪 Testing core analysis...")
        
        # Simple test article
        test_url = "https://www.example.com/test"
        test_text = "This is a simple test article about technology and innovation. It discusses various technical terms and different perspectives on the topic."
        
        context = {
            'user_tier': 'free',
            'user_id': 'test_user'
        }
        
        print("🚀 Starting analysis...")
        result = await coordinator.analyze_core(
            article_url=test_url,
            article_text=test_text,
            user_context=context
        )
        
        print(f"✅ Analysis completed!")
        print(f"Success: {result.get('success')}")
        print(f"Session ID: {result.get('session_id')}")
        
        if result.get('success'):
            results = result.get('results', {})
            print(f"Jargon result: {'✅' if results.get('jargon') else '❌'}")
            print(f"Viewpoints result: {'✅' if results.get('viewpoints') else '❌'}")
        else:
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_analysis()) 