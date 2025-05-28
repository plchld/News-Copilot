#!/usr/bin/env python3
"""Test script for the updated rate limiting system"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"  # Change to production URL if needed
TEST_ARTICLE = "https://www.kathimerini.gr/politics/562876456/o-mitsotakis-gia-tin-toyrkia/"

# Test user credentials (you'll need to provide these)
TEST_EMAIL = "test@example.com"
AUTH_TOKEN = None  # Will be set after login


def send_magic_link(email):
    """Send magic link for authentication"""
    response = requests.post(
        f"{BASE_URL}/api/auth/magic-link",
        json={"email": email}
    )
    print(f"Magic link sent: {response.json()}")
    return response.status_code == 200


def get_profile(token):
    """Get user profile and usage stats"""
    response = requests.get(
        f"{BASE_URL}/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


def test_basic_analysis(token, article_url):
    """Test basic analysis (augment-stream)"""
    print("\n=== Testing Basic Analysis ===")
    start_time = time.time()
    
    response = requests.get(
        f"{BASE_URL}/augment-stream",
        params={"url": article_url},
        headers={"Authorization": f"Bearer {token}"},
        stream=True
    )
    
    # Read the stream
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data:'):
                try:
                    data = json.loads(decoded[5:])
                    print(f"Received: {data.get('type', 'unknown')}")
                except:
                    pass
    
    elapsed = time.time() - start_time
    print(f"Basic analysis completed in {elapsed:.2f} seconds")
    return response.status_code == 200


def test_deep_analysis(token, article_url, analysis_type):
    """Test deep analysis"""
    print(f"\n=== Testing Deep Analysis: {analysis_type} ===")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/deep-analysis",
        json={
            "url": article_url,
            "analysis_type": analysis_type,
            "search_params": {"mode": "on"}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    elapsed = time.time() - start_time
    result = response.json()
    
    if result.get('success'):
        print(f"Deep analysis ({analysis_type}) completed in {elapsed:.2f} seconds")
        print(f"Result keys: {list(result.get('result', {}).keys())}")
    else:
        print(f"Deep analysis failed: {result.get('error')}")
    
    return response.status_code == 200


def main():
    print("=== Rate Limiting Test Suite ===")
    print(f"Testing against: {BASE_URL}")
    print(f"Test article: {TEST_ARTICLE}")
    
    # Step 1: Authentication
    print("\n1. Authentication")
    print("Please provide your auth token (or press Enter to send magic link):")
    token_input = input().strip()
    
    if token_input:
        AUTH_TOKEN = token_input
    else:
        print(f"Sending magic link to: {TEST_EMAIL}")
        if send_magic_link(TEST_EMAIL):
            print("Check your email and paste the token here:")
            AUTH_TOKEN = input().strip()
        else:
            print("Failed to send magic link")
            return
    
    # Step 2: Check initial usage
    print("\n2. Checking initial usage stats")
    profile = get_profile(AUTH_TOKEN)
    print(f"User tier: {profile.get('tier')}")
    print(f"Current usage: {profile.get('usage_this_month')}")
    print(f"Usage limits: {profile.get('usage_limits')}")
    initial_usage = profile.get('usage_this_month', {})
    
    # Step 3: Test basic analysis
    if test_basic_analysis(AUTH_TOKEN, TEST_ARTICLE):
        print("✅ Basic analysis successful")
    else:
        print("❌ Basic analysis failed")
    
    # Step 4: Test deep analyses
    deep_analysis_types = ['fact-check', 'bias', 'timeline', 'expert', 'x-pulse']
    for analysis_type in deep_analysis_types[:2]:  # Test only first 2 to not exhaust limits
        if test_deep_analysis(AUTH_TOKEN, TEST_ARTICLE, analysis_type):
            print(f"✅ {analysis_type} analysis successful")
        else:
            print(f"❌ {analysis_type} analysis failed")
        time.sleep(2)  # Small delay between requests
    
    # Step 5: Check final usage
    print("\n5. Checking final usage stats")
    profile = get_profile(AUTH_TOKEN)
    final_usage = profile.get('usage_this_month', {})
    
    print(f"\nUsage comparison:")
    print(f"Basic analyses: {initial_usage.get('basic_analysis', 0)} → {final_usage.get('basic_analysis', 0)}")
    print(f"Deep analyses: {initial_usage.get('deep_analysis', 0)} → {final_usage.get('deep_analysis', 0)}")
    
    # Verify the counts
    basic_diff = final_usage.get('basic_analysis', 0) - initial_usage.get('basic_analysis', 0)
    deep_diff = final_usage.get('deep_analysis', 0) - initial_usage.get('deep_analysis', 0)
    
    print(f"\n✅ Test Results:")
    print(f"- Basic analysis incremented by: {basic_diff} (expected: 1)")
    print(f"- Deep analysis incremented by: {deep_diff} (expected: 2)")
    
    if basic_diff == 1 and deep_diff == 2:
        print("\n🎉 All tests passed! Rate limiting is working correctly.")
    else:
        print("\n⚠️ Unexpected usage counts. Please check the implementation.")


if __name__ == "__main__":
    main()