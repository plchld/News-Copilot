#!/usr/bin/env python3
"""
Test the comprehensive API system
"""
import requests
import json
import time
from datetime import datetime

# API base URL (when server is running)
BASE_URL = "http://localhost:5001"

def test_api_health():
    """Test API health endpoints"""
    print("\n🏥 TESTING API HEALTH")
    print("-" * 40)
    
    endpoints = [
        "/api/health",
        "/api/agents/health", 
        "/api/articles/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {endpoint}: {data.get('status', 'unknown')}")
            else:
                print(f"✗ {endpoint}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"✗ {endpoint}: Connection error - {e}")

def test_agent_endpoints():
    """Test agent API endpoints"""
    print("\n🤖 TESTING AGENT ENDPOINTS")
    print("-" * 40)
    
    # Test list agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents/list")
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', {})
            print(f"✓ Available agents: {list(agents.keys())}")
        else:
            print(f"✗ List agents failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ List agents error: {e}")
    
    # Test single agent analysis
    test_content = "Το Υπουργικό Συμβούλιο θα συνεδριάσει την Τετάρτη για να συζητήσει σημαντικά θέματα."
    
    try:
        payload = {
            "content": test_content,
            "url": "https://example.com/test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/agents/jargon/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Jargon agent: {data.get('analysis_status', 'unknown')}")
            if data.get('data'):
                print(f"  Duration: {data.get('duration_seconds', 0):.1f}s")
        else:
            print(f"✗ Jargon agent failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ Jargon agent error: {e}")

def test_article_endpoints():
    """Test article API endpoints"""
    print("\n📄 TESTING ARTICLE ENDPOINTS")
    print("-" * 40)
    
    # Test article stats
    try:
        response = requests.get(f"{BASE_URL}/api/articles/stats")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"✓ Article stats: {stats.get('total_articles', 0)} articles")
        else:
            print(f"✗ Article stats failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Article stats error: {e}")
    
    # Test list articles
    try:
        response = requests.get(f"{BASE_URL}/api/articles/list?limit=5")
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✓ List articles: {len(articles)} found")
        else:
            print(f"✗ List articles failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ List articles error: {e}")

def test_full_workflow():
    """Test complete workflow: process article -> analyze -> retrieve"""
    print("\n🔄 TESTING FULL WORKFLOW")
    print("-" * 40)
    
    # Sample AMNA URL for testing
    test_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print(f"📝 Processing article: {test_url[:60]}...")
    
    try:
        # Step 1: Process article
        payload = {
            "url": test_url,
            "enrich": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/articles/process",
            json=payload,
            timeout=120  # Long timeout for processing
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                article_id = data.get('article_id')
                print(f"✓ Article processed: ID {article_id}")
                print(f"  Enriched: {data.get('enriched', False)}")
                print(f"  Duration: {data.get('enrichment_duration', 0):.1f}s")
                
                # Step 2: Retrieve article
                if article_id:
                    time.sleep(1)  # Brief pause
                    
                    retrieve_response = requests.get(f"{BASE_URL}/api/articles/{article_id}")
                    if retrieve_response.status_code == 200:
                        retrieve_data = retrieve_response.json()
                        print(f"✓ Article retrieved successfully")
                        
                        # Check enrichments
                        enrichments_response = requests.get(f"{BASE_URL}/api/articles/{article_id}/enrichments")
                        if enrichments_response.status_code == 200:
                            enrich_data = enrichments_response.json()
                            analyses = enrich_data.get('available_analyses', [])
                            print(f"✓ Available enrichments: {analyses}")
                        
                    else:
                        print(f"✗ Article retrieval failed: HTTP {retrieve_response.status_code}")
            else:
                print(f"✗ Article processing failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"✗ Article processing failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ Workflow test error: {e}")

def test_api_info():
    """Test API info endpoint"""
    print("\n📋 API INFORMATION")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service: {data.get('service', 'Unknown')}")
            print(f"✓ Version: {data.get('version', 'Unknown')}")
            print(f"✓ Available agents: {data.get('available_agents', [])}")
        else:
            print(f"✗ API info failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ API info error: {e}")

def main():
    """Run comprehensive API tests"""
    print("=" * 60)
    print("🚀 NEWS AGGREGATOR API v2 - COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"🌐 Testing API at: {BASE_URL}")
    print(f"⚠️  Make sure the server is running: python web_app.py")
    
    # Wait a moment to ensure user sees the message
    time.sleep(2)
    
    test_api_info()
    test_api_health()
    test_agent_endpoints()
    test_article_endpoints()
    
    # Ask user if they want to run full workflow test
    print(f"\n❓ Run full workflow test? (This will process a real AMNA article)")
    print(f"   This test takes 1-2 minutes and requires API key.")
    user_input = input("   Continue? (y/n): ").lower().strip()
    
    if user_input in ['y', 'yes']:
        test_full_workflow()
    else:
        print("⏭️  Skipping full workflow test")
    
    print("\n" + "=" * 60)
    print("✅ API TESTING COMPLETED!")
    print("\n📖 Available API endpoints:")
    print(f"   🔍 API Info: {BASE_URL}/api/info")
    print(f"   🤖 Agents: {BASE_URL}/api/agents/list")
    print(f"   📄 Articles: {BASE_URL}/api/articles/stats")
    print(f"   🌐 Web Interface: {BASE_URL}/")

if __name__ == "__main__":
    main()