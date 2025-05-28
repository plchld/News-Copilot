#!/usr/bin/env python3
"""Test viewpoints through the restarted server"""

import requests
import json

SERVER_URL = "http://127.0.0.1:8080"

def test_server():
    """Test the server's viewpoints functionality"""
    
    article_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print("Testing viewpoints on restarted server...")
    print(f"Server: {SERVER_URL}")
    print(f"Article: {article_url}")
    print("="*60)
    
    # Test the augment-stream endpoint
    print("\nCalling /augment-stream...")
    
    try:
        response = requests.get(
            f"{SERVER_URL}/augment-stream",
            params={"url": article_url},
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=60
        )
        
        print(f"Response status: {response.status_code}\n")
        
        if response.status_code == 200:
            events = []
            final_result = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    # Collect all events
                    if line_str.strip():
                        events.append(line_str)
                        
                        # Print progress events
                        if "event: progress" in line_str or "event: error" in line_str:
                            print(f"  {line_str}")
                        
                        # Extract final result
                        if line_str.startswith("data:") and "final_result" in line_str:
                            try:
                                json_str = line_str[5:].strip()
                                final_result = json.loads(json_str)
                            except Exception as e:
                                print(f"Error parsing final result: {e}")
            
            print(f"\nTotal events received: {len(events)}")
            
            if final_result:
                print("\n" + "="*60)
                print("FINAL RESULT ANALYSIS:")
                print("="*60)
                
                # Check viewpoints specifically
                viewpoints_data = final_result.get('viewpoints', {})
                print(f"\nViewpoints data type: {type(viewpoints_data)}")
                
                if isinstance(viewpoints_data, dict):
                    viewpoints_list = viewpoints_data.get('viewpoints', [])
                    print(f"Viewpoints array found: {len(viewpoints_list)} items")
                    
                    if viewpoints_list:
                        print("\nViewpoints content:")
                        for i, vp in enumerate(viewpoints_list[:3], 1):
                            print(f"\n{i}. {vp[:150]}..." if len(vp) > 150 else f"\n{i}. {vp}")
                    else:
                        print("❌ Viewpoints array is empty!")
                else:
                    print(f"❌ Unexpected viewpoints structure: {viewpoints_data}")
                
                # Also check jargon for comparison
                jargon_data = final_result.get('jargon', {})
                if isinstance(jargon_data, dict):
                    terms = jargon_data.get('terms', [])
                    print(f"\n\nJargon terms found: {len(terms)} (for comparison)")
            else:
                print("\n❌ No final result received!")
                
        else:
            print(f"Error response: {response.status_code}")
            print(response.text[:500])
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_server()