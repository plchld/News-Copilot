#!/usr/bin/env python3
"""Test the complete UI flow with the unified API"""

import requests
import json
import time

def test_unified_flow():
    """Test the unified API flow that the UI uses"""
    
    base_url = "http://localhost:8080"
    article_url = "https://www.kathimerini.gr/politics/562935640/o-al-tsipras-apenanti-se-dilimmata/"
    
    print("🧪 Testing Unified API Flow\n")
    print("=" * 60)
    
    # Test 1: Basic analysis (free tier)
    print("\n1️⃣ Testing basic analysis (jargon + viewpoints)")
    response = requests.post(
        f"{base_url}/api/analyze",
        json={
            "url": article_url,
            "types": ["jargon", "viewpoints"]
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", {})
        
        # Check jargon
        if "jargon" in results:
            jargon = results["jargon"]
            if "markdown_content" in jargon:
                print(f"✅ Jargon: Markdown content ({len(jargon['markdown_content'])} chars)")
            else:
                print(f"✅ Jargon: Structured data")
        
        # Check viewpoints
        if "viewpoints" in results:
            viewpoints = results["viewpoints"]
            if "markdown_content" in viewpoints:
                print(f"✅ Viewpoints: Markdown content ({len(viewpoints['markdown_content'])} chars)")
            else:
                print(f"✅ Viewpoints: Structured data")
                
        print(f"⏱️  Total time: {data['metadata']['total_time_seconds']}s")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "=" * 60)
    
    # Test 2: Multiple analyses including fact-check
    print("\n2️⃣ Testing multiple analyses (including fact-check)")
    response = requests.post(
        f"{base_url}/api/analyze",
        json={
            "url": article_url,
            "types": ["jargon", "viewpoints", "fact-check", "bias"]
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 207]:
        data = response.json()
        results = data.get("results", {})
        errors = data.get("errors", {})
        
        print("\nResults:")
        for analysis_type, result in results.items():
            if isinstance(result, dict) and "markdown_content" in result:
                print(f"  ✅ {analysis_type}: Markdown ({len(result['markdown_content'])} chars)")
            else:
                print(f"  ✅ {analysis_type}: Structured data")
        
        if errors:
            print("\nErrors:")
            for analysis_type, error in errors.items():
                print(f"  ❌ {analysis_type}: {error}")
        
        metadata = data.get("metadata", {})
        print(f"\n📊 Summary:")
        print(f"  - Requested: {metadata.get('analyses_requested', 'N/A')}")
        print(f"  - Completed: {metadata.get('analyses_completed', 'N/A')}")
        print(f"  - Total time: {metadata.get('total_time_seconds', 'N/A')}s")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "=" * 60)
    
    # Test 3: Single analysis (simulating tab switch)
    print("\n3️⃣ Testing single analysis (fact-check only)")
    response = requests.post(
        f"{base_url}/api/analyze",
        json={
            "url": article_url,
            "types": ["fact-check"]
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", {})
        
        if "fact-check" in results:
            fact_check = results["fact-check"]
            if "markdown_content" in fact_check:
                print(f"✅ Fact-check: Markdown content")
                print(f"   Preview: {fact_check['markdown_content'][:200]}...")
            else:
                print(f"❌ Fact-check returned non-markdown data")
                print(f"   Keys: {list(fact_check.keys())}")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_unified_flow()