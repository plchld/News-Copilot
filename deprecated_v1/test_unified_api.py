#!/usr/bin/env python3
"""Test the unified API endpoint"""

import requests
import json
import sys
from typing import List

def test_unified_api(url: str, types: List[str], api_base: str = "http://localhost:8080"):
    """Test the unified /api/analyze endpoint"""
    
    endpoint = f"{api_base}/api/analyze"
    
    print(f"Testing unified API:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Article: {url}")
    print(f"  Types: {types}")
    print("-" * 50)
    
    try:
        # Make request
        response = requests.post(
            endpoint,
            json={"url": url, "types": types},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Parse response
        data = response.json()
        
        # Show results
        results = data.get("results", {})
        errors = data.get("errors", {})
        metadata = data.get("metadata", {})
        
        print(f"\n✅ Successful analyses: {len(results)}")
        for analysis_type, result in results.items():
            print(f"  - {analysis_type}: ", end="")
            if isinstance(result, dict) and "markdown_content" in result:
                print(f"Markdown ({len(result['markdown_content'])} chars)")
            else:
                print(f"Structured data")
        
        if errors:
            print(f"\n❌ Failed analyses: {len(errors)}")
            for analysis_type, error in errors.items():
                print(f"  - {analysis_type}: {error}")
        
        print(f"\n📊 Metadata:")
        print(f"  - Total time: {metadata.get('total_time_seconds', 'N/A')}s")
        print(f"  - Requested: {metadata.get('analyses_requested', 'N/A')}")
        print(f"  - Completed: {metadata.get('analyses_completed', 'N/A')}")
        
        return response.status_code == 200 or response.status_code == 207
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    # Test article
    test_url = "https://www.kathimerini.gr/politics/562935640/o-al-tsipras-apenanti-se-dilimmata/"
    
    # Test different combinations
    test_cases = [
        # Free tier analyses
        ["jargon", "viewpoints"],
        ["fact-check"],
        ["bias"],
        
        # All free tier
        ["jargon", "viewpoints", "fact-check", "bias"],
        
        # Premium (will fail without auth)
        ["timeline", "expert"],
        
        # Mix of free and premium
        ["jargon", "timeline", "x-pulse"],
        
        # Single analysis
        ["viewpoints"],
        
        # Invalid type
        ["jargon", "invalid-type"]
    ]
    
    print("🧪 Testing Unified API\n")
    
    for i, types in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_cases)}")
        print(f"{'='*60}")
        
        success = test_unified_api(test_url, types)
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
        
        if i < len(test_cases):
            input("\nPress Enter for next test...")

if __name__ == "__main__":
    main()