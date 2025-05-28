#!/usr/bin/env python3
"""
Local testing script for News Copilot API using the unified endpoint
"""

import requests
import json
import time
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Configuration
API_BASE = "http://localhost:8080"
TEST_URLS = [
    "https://www.kathimerini.gr/economy/562737833/i-agora-ergasias-stin-ee-deixnei-simadia-antochis/",
    "https://www.protothema.gr/greece/article/1479445/pagkosmio-rekor-zestis-gia-ton-marti/",
    "https://www.tanea.gr/2024/03/15/greece/oikonomia/eurostat-mikri-ypoxorisi-tou-plithorismou-ton-fevrouario/"
]

def print_header():
    """Print script header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"News Copilot - Local Testing Script")
    print(f"{'='*60}{Style.RESET_ALL}\n")

def test_unified_api():
    """Test the unified analysis API"""
    
    # Test article
    test_url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print("🧪 Testing Unified Analysis API")
    print("=" * 60)
    print(f"Article: {test_url}")
    print()
    
    # Test different analysis combinations
    test_cases = [
        {
            "name": "Basic Analysis (Free Tier)",
            "types": ["jargon", "viewpoints"]
        },
        {
            "name": "Fact Check Only",
            "types": ["fact-check"]
        },
        {
            "name": "Multiple Free Analyses",
            "types": ["jargon", "viewpoints", "fact-check", "bias"]
        }
    ]
    
    for test_case in test_cases:
        print(f"📋 {test_case['name']}")
        print(f"   Types: {test_case['types']}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE}/api/analyze",
                json={
                    "url": test_url,
                    "types": test_case['types']
                },
                timeout=180
            )
            
            elapsed = time.time() - start_time
            print(f"   ⏱️  {elapsed:.2f}s | Status: {response.status_code}")
            
            if response.status_code in [200, 207]:
                data = response.json()
                results = data.get('results', {})
                errors = data.get('errors', {})
                
                print(f"   ✅ Success: {len(results)}/{len(test_case['types'])}")
                
                for analysis_type in test_case['types']:
                    if analysis_type in results:
                        result = results[analysis_type]
                        if isinstance(result, dict) and 'markdown_content' in result:
                            print(f"      {analysis_type}: {len(result['markdown_content'])} chars")
                        else:
                            print(f"      {analysis_type}: structured data")
                    elif analysis_type in errors:
                        print(f"      {analysis_type}: ❌ {errors[analysis_type]}")
                        
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print()

def test_health():
    """Test API health"""
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return False

def test_analysis_types():
    """Test the analysis types endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/analyze/types", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("📋 Available Analysis Types:")
            print(f"   Free tier: {data.get('free_tier', [])}")
            print(f"   Premium tier: {data.get('premium_tier', [])}")
            return True
        else:
            print(f"❌ Types endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Types endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print_header()
    
    # Test 1: Health check
    if not test_health():
        sys.exit(1)
    
    # Test 2: Analysis types
    test_analysis_types()
    
    # Test 3: Unified API
    test_unified_api()
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Testing complete!")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Next steps:{Style.RESET_ALL}")
    print("1. Open http://localhost:3000 to test the web interface")
    print("2. Try different Greek news URLs")
    print("3. Check the API logs for detailed information")
    print("\nFor more tests, use: make test")

if __name__ == "__main__":
    main()