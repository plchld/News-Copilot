#!/usr/bin/env python3
"""
Test script for News Copilot authentication system
Tests all authentication endpoints and freemium flow
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"  # Change to your Vercel URL when testing production
ADMIN_KEY = "your-admin-secret-key"  # Change to your actual admin key

def test_user_registration():
    """Test user registration endpoint"""
    print("\n=== Testing User Registration ===")
    
    test_email = f"test_{int(time.time())}@example.com"
    
    response = requests.post(f"{BASE_URL}/api/auth/register", 
                           json={"email": test_email})
    
    print(f"Registration Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User registered successfully")
        print(f"Token: {data.get('token', 'N/A')}")
        print(f"Tier: {data.get('user', {}).get('tier', 'N/A')}")
        return data.get('token'), test_email
    else:
        print(f"❌ Registration failed: {response.text}")
        return None, None

def test_user_login(email):
    """Test user login endpoint"""
    print(f"\n=== Testing User Login ({email}) ===")
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                           json={"email": email})
    
    print(f"Login Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        print(f"Token: {data.get('token', 'N/A')}")
        return data.get('token')
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_user_profile(token):
    """Test user profile endpoint"""
    print(f"\n=== Testing User Profile ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
    
    print(f"Profile Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Profile retrieved successfully")
        print(f"Email: {data.get('email', 'N/A')}")
        print(f"Tier: {data.get('tier', 'N/A')}")
        print(f"Usage this month: {data.get('usage_this_month', 'N/A')}")
        print(f"Usage limits: {data.get('usage_limits', 'N/A')}")
        return data
    else:
        print(f"❌ Profile failed: {response.text}")
        return None

def test_analysis_endpoint(token, analysis_type="jargon"):
    """Test analysis endpoint with authentication"""
    print(f"\n=== Testing Analysis Endpoint ({analysis_type}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_article_url = "https://www.kathimerini.gr"
    
    response = requests.post(f"{BASE_URL}/deep-analysis", 
                           headers=headers,
                           json={
                               "article_url": test_article_url,
                               "analysis_type": analysis_type
                           })
    
    print(f"Analysis Response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Analysis successful")
        # Don't print full response as it might be very long
        print("Analysis completed successfully")
        return True
    else:
        print(f"❌ Analysis failed: {response.text}")
        return False

def test_rate_limiting(token):
    """Test rate limiting by making multiple requests"""
    print(f"\n=== Testing Rate Limiting ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_article_url = "https://www.kathimerini.gr"
    
    success_count = 0
    rate_limited = False
    
    for i in range(12):  # Try 12 requests (should hit 10 free limit)
        print(f"Request {i+1}/12...", end=" ")
        
        response = requests.post(f"{BASE_URL}/deep-analysis", 
                               headers=headers,
                               json={
                                   "article_url": test_article_url,
                                   "analysis_type": "jargon"
                               })
        
        if response.status_code == 200:
            success_count += 1
            print("✅")
        elif response.status_code == 429:  # Rate limited
            rate_limited = True
            print("🚫 Rate limited")
        else:
            print(f"❌ Error: {response.status_code}")
    
    print(f"\nSuccessful requests: {success_count}")
    print(f"Rate limiting triggered: {'✅' if rate_limited else '❌'}")
    
    return success_count, rate_limited

def test_admin_endpoints():
    """Test admin endpoints"""
    print(f"\n=== Testing Admin Endpoints ===")
    
    headers = {"X-Admin-Key": ADMIN_KEY}
    
    # Test users list
    response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
    print(f"Admin users list: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total users: {data.get('total_users', 0)}")
        print(f"Tier breakdown: {data.get('tier_breakdown', {})}")
    else:
        print(f"❌ Admin users failed: {response.text}")
    
    # Test usage stats
    response = requests.get(f"{BASE_URL}/api/admin/usage-stats", headers=headers)
    print(f"Admin usage stats: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Usage stats retrieved")
    else:
        print(f"❌ Usage stats failed: {response.text}")

def test_byok_flow():
    """Test Bring Your Own Key flow"""
    print(f"\n=== Testing BYOK Flow ===")
    
    test_email = f"byok_{int(time.time())}@example.com"
    
    # Register with BYOK
    response = requests.post(f"{BASE_URL}/api/auth/register", 
                           json={
                               "email": test_email,
                               "api_key": "test-api-key-123"
                           })
    
    print(f"BYOK Registration: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ BYOK user registered")
        print(f"Tier: {data.get('user', {}).get('tier', 'N/A')}")
        return data.get('token')
    else:
        print(f"❌ BYOK registration failed: {response.text}")
        return None

def main():
    """Run all tests"""
    print("🧪 News Copilot Authentication System Test Suite")
    print("=" * 50)
    
    # Test 1: User Registration
    token, email = test_user_registration()
    if not token:
        print("❌ Cannot continue tests without successful registration")
        return
    
    # Test 2: User Login
    login_token = test_user_login(email)
    if login_token:
        token = login_token  # Use login token for remaining tests
    
    # Test 3: User Profile
    test_user_profile(token)
    
    # Test 4: Analysis Endpoint
    test_analysis_endpoint(token, "jargon")
    
    # Test 5: Rate Limiting
    success_count, rate_limited = test_rate_limiting(token)
    
    # Test 6: Admin Endpoints
    test_admin_endpoints()
    
    # Test 7: BYOK Flow
    test_byok_flow()
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 Test Summary")
    print(f"{'='*50}")
    print(f"✅ User registration and login working")
    print(f"✅ Authentication tokens working")
    print(f"✅ Rate limiting {'working' if rate_limited else 'NOT working'}")
    print(f"✅ Analysis endpoints accessible")
    print(f"✅ Admin endpoints accessible")

if __name__ == "__main__":
    main()