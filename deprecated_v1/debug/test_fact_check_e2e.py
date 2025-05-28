#!/usr/bin/env python3
"""
End-to-end test for fact check analysis using the unified API
"""

import requests
import json
import time

def test_fact_check_e2e():
    """Test fact check analysis end-to-end using unified API"""
    
    # Test article URL
    test_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    # Use unified API endpoint
    api_url = "http://localhost:8080/api/analyze"
    
    print("🧪 Testing Fact Check Analysis (E2E)")
    print("=" * 50)
    print(f"URL: {test_url}")
    print(f"API: {api_url}")
    print()
    
    try:
        print("📡 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            json={
                "url": test_url,
                "types": ["fact-check"]
            },
            timeout=180
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Completed in {elapsed:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code in [200, 207]:
            data = response.json()
            
            if 'results' in data and 'fact-check' in data['results']:
                result = data['results']['fact-check']
                print("✅ Fact-check analysis successful")
                
                if isinstance(result, dict) and 'markdown_content' in result:
                    content = result['markdown_content']
                    print(f"📝 Content length: {len(content)} characters")
                    print(f"📄 Sample: {content[:200]}...")
                else:
                    print(f"📊 Result type: {type(result)}")
                    
            else:
                print("❌ No fact-check results found")
                
            # Show metadata
            if 'metadata' in data:
                metadata = data['metadata']
                print(f"📊 Metadata: {metadata}")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fact_check_e2e()