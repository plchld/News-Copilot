#!/usr/bin/env python
"""
Simple test script to verify Claude integration is working
"""
import os
import sys
import django
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.news_aggregator.agents.jargon_agent import JargonAgent


async def test_claude_connection():
    """Simple test to verify Claude is working"""
    print("🔍 Testing Claude connection with Jargon Agent...")
    
    # Simple test content
    test_content = """
    Η κυβέρνηση ανακοίνωσε νέα μέτρα για την AI (τεχνητή νοημοσύνη) και 
    την εφαρμογή GDPR protocols στα δημόσια συστήματα.
    """
    
    try:
        agent = JargonAgent()
        print(f"✅ Agent created: {agent.config.name}")
        print(f"📱 Model: {agent.config.default_model.value}")
        
        result = await agent.process(test_content)
        
        if result.success:
            print("✅ Claude API call successful!")
            print(f"📊 Data received: {bool(result.data)}")
            if result.data and 'terms' in result.data:
                print(f"📚 Found {len(result.data['terms'])} terms")
                for term in result.data['terms'][:2]:  # Show first 2 terms
                    print(f"   - {term.get('term', 'N/A')}: {term.get('explanation', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Agent failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_claude_connection())
    
    if success:
        print("\n🎉 Claude migration is working!")
    else:
        print("\n💥 Claude migration has issues - check ANTHROPIC_API_KEY")
        print("   Set it in your environment: export ANTHROPIC_API_KEY=your_key")