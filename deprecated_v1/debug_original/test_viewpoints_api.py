#!/usr/bin/env python3
"""Test viewpoints API endpoint with detailed output"""

import requests
import json
import time

def test_viewpoints_api():
    """Test the viewpoints analysis through the API"""
    article_url = 'https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/'
    url = f'http://localhost:8080/augment-stream?url={article_url}'
    
    print("Testing viewpoints analysis via API...")
    print(f"Article URL: {article_url}")
    print(f"Request URL: {url}")
    print("\nSending request...")
    
    try:
        response = requests.get(url, stream=True)
        print(f"Response status: {response.status_code}")
        
        events = []
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                print(f"Raw line: {decoded}")
                
                if decoded.startswith('data: '):
                    try:
                        event_data = json.loads(decoded[6:])
                        events.append(event_data)
                        
                        # Pretty print the event
                        if event_data.get('type') == 'analysis_complete':
                            print("\n=== ANALYSIS COMPLETE ===")
                            results = event_data.get('data', {}).get('results', {})
                            
                            # Check viewpoints specifically
                            if 'viewpoints' in results:
                                vp_data = results['viewpoints']
                                print(f"\nViewpoints data type: {type(vp_data)}")
                                print(f"Viewpoints data: {json.dumps(vp_data, ensure_ascii=False, indent=2)}")
                                
                                if isinstance(vp_data, dict) and 'viewpoints' in vp_data:
                                    viewpoints_list = vp_data['viewpoints']
                                    print(f"\nFound {len(viewpoints_list)} viewpoints")
                                elif isinstance(vp_data, list):
                                    print(f"\nFound {len(vp_data)} viewpoints (array format)")
                                else:
                                    print(f"\nUnexpected viewpoints format: {vp_data}")
                            else:
                                print("\nNo viewpoints in results")
                        else:
                            print(f"\nEvent type: {event_data.get('type')}")
                            if 'data' in event_data:
                                print(f"Event data: {json.dumps(event_data['data'], ensure_ascii=False, indent=2)}")
                                
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        
        print(f"\nTotal events received: {len(events)}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_viewpoints_api()