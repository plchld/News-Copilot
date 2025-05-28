#!/usr/bin/env python3
"""Test viewpoints debug endpoint"""

import requests
import json

SERVER_URL = "http://127.0.0.1:8080"

def test_debug_endpoint():
    """Test the debug endpoint for detailed error info"""
    
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print("Testing debug endpoint for viewpoints...")
    print("="*60)
    
    payload = {
        "url": article_url,
        "agent": "viewpoints",
        "debug_level": "verbose"
    }
    
    try:
        print("Sending request to /api/debug/agent...")
        response = requests.post(
            f"{SERVER_URL}/api/debug/agent",
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Success: {data.get('success')}")
            
            if data.get('debug_report'):
                print("\n" + "="*60)
                print("DEBUG REPORT:")
                print("="*60)
                print(data['debug_report'])
            
            if data.get('error'):
                print(f"\nError: {data['error']}")
                
            if data.get('result'):
                viewpoints = data['result'].get('viewpoints', [])
                print(f"\nViewpoints found: {len(viewpoints)}")
                
        else:
            print(f"\nError response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text[:1000])
                
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 120 seconds")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_debug_endpoint()