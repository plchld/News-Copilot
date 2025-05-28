#!/usr/bin/env python3
"""Test script to debug agent failures"""

import sys
sys.path.append('.')
import asyncio
from api.core.analysis_handlers import AnalysisHandler

async def test():
    handler = AnalysisHandler()
    url = 'https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/'
    
    print('Testing jargon analysis failure...')
    try:
        chunk_count = 0
        async for chunk in handler.get_augmentations_stream(url):
            chunk_count += 1
            print(f'Chunk {chunk_count}: {chunk[:150]}...')
            if 'jargon analysis failed' in chunk.lower() or 'error' in chunk.lower():
                print('FOUND ERROR!')
                print(f'Full chunk: {chunk}')
                break
            if chunk_count > 20:
                break
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test()) 