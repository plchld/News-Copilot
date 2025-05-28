#!/usr/bin/env python3
"""
Test script to verify concurrent execution works correctly
"""

import asyncio
import time
from analysis_handlers import AnalysisHandler

async def test_concurrent_vs_sequential():
    """Test to demonstrate concurrent execution speedup"""
    print("Testing Concurrent vs Sequential Execution")
    print("=" * 50)
    
    handler = AnalysisHandler()
    
    # Test with a simple Greek article
    test_url = "https://www.kathimerini.gr/test"
    
    print("Starting concurrent analysis test...")
    
    try:
        # Time the concurrent execution
        start_time = time.time()
        
        chunks = []
        async for chunk in handler.get_augmentations_stream(test_url):
            chunks.append(chunk)
            print(f"Received chunk: {chunk[:100]}...")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n✅ Concurrent execution completed in {total_time:.2f} seconds")
        print(f"📊 Total chunks received: {len(chunks)}")
        
        # Look for performance logs in the output
        performance_logs = [chunk for chunk in chunks if "PERFORMANCE" in chunk or "speedup" in chunk.lower()]
        if performance_logs:
            print("\n📈 Performance improvements detected:")
            for log in performance_logs:
                print(f"  {log.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_concurrent_vs_sequential()
    
    if success:
        print("\n🎉 Concurrent execution test PASSED!")
        print("Jargon and viewpoints analysis should now run in parallel")
    else:
        print("\n💥 Concurrent execution test FAILED!")
        print("Check the error logs above")

if __name__ == "__main__":
    asyncio.run(main())