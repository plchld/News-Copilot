#!/usr/bin/env python3
"""Test the debug endpoint through HTTP (not direct imports)"""

import requests
import json

SERVER_URL = "http://127.0.0.1:8080"

def test_debug_endpoint():
    """Test the /api/debug/agent endpoint"""
    
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print(f"Testing debug endpoint at {SERVER_URL}/api/debug/agent")
    print("="*60)
    
    payload = {
        "url": article_url,
        "agent": "viewpoints",
        "debug_level": "normal"
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/debug/agent",
            json=payload,
            timeout=30  # 30 second timeout
        )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess: {data.get('success')}")
            print(f"Agent: {data.get('agent')}")
            print(f"Execution time: {data.get('execution_time_ms')}ms")
            
            if data.get('result'):
                viewpoints = data['result'].get('viewpoints', [])
                print(f"\nViewpoints found: {len(viewpoints)}")
                
                if viewpoints:
                    print("\nFirst viewpoint:")
                    print(viewpoints[0][:200] + "..." if len(viewpoints[0]) > 200 else viewpoints[0])
            
            if data.get('error'):
                print(f"\nError: {data['error']}")
                
            # Show debug report if available
            if data.get('debug_report'):
                print("\n" + "="*60)
                print("DEBUG REPORT:")
                print("="*60)
                print(data['debug_report'][:1000] + "..." if len(data['debug_report']) > 1000 else data['debug_report'])
        else:
            print(f"\nError response:")
            print(response.text[:500])
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_debug_endpoint()