#!/usr/bin/env python3
"""Test viewpoints through the local Flask server"""

import requests
import json
import time

# Server URL
SERVER_URL = "http://127.0.0.1:8080"

def test_viewpoints_via_server():
    """Test viewpoints using the server API"""
    
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print(f"Testing viewpoints through server at {SERVER_URL}")
    print(f"Article: {article_url}")
    print("="*60)
    
    # First, test the augment-stream endpoint which includes viewpoints
    print("\n1. Testing /augment-stream endpoint (SSE)...")
    
    try:
        response = requests.get(
            f"{SERVER_URL}/augment-stream",
            params={"url": article_url},
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("\nStreaming events:")
            final_result = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"  {line_str}")
                    
                    # Parse SSE format
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            if "final_result" in line_str:
                                final_result = data
                        except:
                            pass
            
            if final_result:
                print("\n\nFINAL RESULT:")
                print(json.dumps(final_result, indent=2, ensure_ascii=False))
                
                # Check viewpoints specifically
                viewpoints = final_result.get('viewpoints', {}).get('viewpoints', [])
                print(f"\n\nViewpoints found: {len(viewpoints)}")
                if viewpoints:
                    for i, vp in enumerate(viewpoints[:3], 1):
                        print(f"\n{i}. {vp[:200]}...")
                else:
                    print("❌ No viewpoints returned!")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error calling augment-stream: {e}")
    
    # Also test the debug endpoint if available
    print("\n\n2. Testing /api/debug/agent endpoint...")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/debug/agent",
            json={
                "url": article_url,
                "agent": "viewpoints",
                "debug_level": "verbose"
            }
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Execution time: {data.get('execution_time_ms')}ms")
            
            if data.get('success'):
                result = data.get('result', {})
                viewpoints = result.get('viewpoints', [])
                print(f"Viewpoints found: {len(viewpoints)}")
                
                # Show debug report
                if data.get('debug_report'):
                    print("\n\nDEBUG REPORT:")
                    print(data['debug_report'])
            else:
                print(f"Error: {data.get('error')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error calling debug endpoint: {e}")


if __name__ == "__main__":
    test_viewpoints_via_server()