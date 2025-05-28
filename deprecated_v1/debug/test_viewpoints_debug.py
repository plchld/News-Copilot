#!/usr/bin/env python3
"""Test viewpoints analysis with detailed logging"""

import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.grok_client import GrokClient
from api.agents.viewpoints_agent import ViewpointsAgent
from api.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_viewpoints():
    """Test viewpoints analysis with problematic article"""
    config = get_config()
    grok_client = GrokClient(api_key=config.XAI_API_KEY)
    
    # Create viewpoints agent
    agent = ViewpointsAgent.create(grok_client)
    
    # Test article
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    article_text = """
    Η Τουρκία επιδιώκει στρατηγική συνεργασία με τις ΗΠΑ υπό όρους που περιλαμβάνουν
    την άρση των κυρώσεων για τους S-400 και την επανένταξη στο πρόγραμμα F-35.
    Οι Τούρκοι αξιωματούχοι τονίζουν ότι η χώρα τους είναι απαραίτητος σύμμαχος
    για την σταθερότητα στη Μέση Ανατολή.
    """
    
    # Build context
    context = {
        'article_url': article_url,
        'article_text': article_text.strip(),
        'session_id': 'test_viewpoints_debug'
    }
    
    print(f"\nTesting ViewpointsAgent with article: {article_url}")
    print(f"Article text preview: {article_text[:200]}...")
    
    # Execute analysis
    try:
        result = await agent.execute(context)
        
        print(f"\nResult success: {result.success}")
        print(f"Result data: {result.data}")
        
        if result.success and result.data:
            viewpoints = result.data.get('viewpoints', [])
            print(f"\nFound {len(viewpoints)} viewpoints:")
            for i, vp in enumerate(viewpoints, 1):
                print(f"\n{i}. {vp.get('perspective', 'No perspective')}")
                print(f"   Argument: {vp.get('argument', 'No argument')}")
                print(f"   Source: {vp.get('source', 'No source')}")
        else:
            print(f"\nError: {result.error}")
            
    except Exception as e:
        print(f"\nException during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_viewpoints())