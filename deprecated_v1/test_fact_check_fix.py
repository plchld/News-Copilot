#!/usr/bin/env python3
"""
Test script to verify fact check analysis using the new unified API
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:8080"

def test_fact_check_analysis():
    """Test fact check analysis using the new unified API"""
    
    # Test URL that was causing issues
    test_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print("🧪 Testing Fact Check Analysis with Unified API")
    print("=" * 60)
    print(f"Test URL: {test_url}")
    print()
    
    try:
        print("📡 Sending fact check analysis request to unified API...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/api/analyze",
            json={
                "url": test_url,
                "types": ["fact-check"]
            },
            timeout=180  # 3 minute timeout
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Request completed in {elapsed:.2f} seconds")
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 207]:  # 200 = success, 207 = partial success
            try:
                data = response.json()
                print("✅ JSON parsing successful")
                
                # Check unified API response structure
                if 'results' in data:
                    results = data['results']
                    print(f"✅ Results structure valid")
                    
                    if 'fact-check' in results:
                        fact_check_result = results['fact-check']
                        print(f"✅ Fact-check analysis present")
                        
                        # Check if it's markdown content or structured data
                        if isinstance(fact_check_result, dict):
                            if 'markdown_content' in fact_check_result:
                                content = fact_check_result['markdown_content']
                                print(f"✅ Found markdown content ({len(content)} characters)")
                                print(f"📝 Sample content: {content[:200]}...")
                            elif 'claims' in fact_check_result:
                                claims = fact_check_result['claims']
                                print(f"✅ Found {len(claims)} claims")
                                
                                # Show first claim as sample
                                if claims:
                                    first_claim = claims[0]
                                    print(f"📝 Sample claim: {first_claim.get('claim', 'N/A')[:100]}...")
                            else:
                                print(f"✅ Fact-check data structure: {list(fact_check_result.keys())}")
                        else:
                            print(f"✅ Fact-check result type: {type(fact_check_result)}")
                    else:
                        print("❌ No fact-check results found")
                        
                    # Check for errors
                    if 'errors' in data and data['errors']:
                        errors = data['errors']
                        print(f"⚠️  Some analyses failed: {errors}")
                        
                    # Show metadata
                    if 'metadata' in data:
                        metadata = data['metadata']
                        print(f"📊 Metadata:")
                        print(f"   - Total time: {metadata.get('total_time_seconds', 'N/A')}s")
                        print(f"   - Requested: {metadata.get('analyses_requested', 'N/A')}")
                        print(f"   - Completed: {metadata.get('analyses_completed', 'N/A')}")
                        
                else:
                    print("❌ No results in response")
                    print(f"Response keys: {list(data.keys())}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Raw response: {response.text[:200]}...")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
                if 'details' in error_data:
                    print(f"Details: {error_data['details']}")
            except:
                print(f"Raw error response: {response.text[:200]}...")
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 3 minutes")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_fact_check_analysis() 