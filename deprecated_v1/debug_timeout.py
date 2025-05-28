#!/usr/bin/env python3
"""Debug script to test the specific URL that was timing out"""

import asyncio
import sys
sys.path.append('.')

async def test_specific_url():
    from api.analysis_handlers import AnalysisHandler
    
    handler = AnalysisHandler()
    url = 'https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/'
    
    print(f'Testing specific URL that timed out: {url}')
    
    try:
        # Test the streaming function directly
        chunk_count = 0
        async for chunk in handler.get_augmentations_stream(url):
            chunk_count += 1
            print(f'Chunk {chunk_count}: {chunk[:100]}...')
            if chunk_count > 10:  # Limit output
                print("... (truncated)")
                break
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_url()) 