#!/usr/bin/env python3
"""
Test HTTP-based Supabase integration
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_http_supabase():
    """Test HTTP-based Supabase connection"""
    print("🧪 Testing HTTP Supabase Integration")
    print("=" * 40)
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"SUPABASE_ANON_KEY: {'✅ Set' if supabase_anon_key else '❌ Missing'}")
    print(f"SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_service_key else '❌ Missing'}")
    
    if not all([supabase_url, supabase_anon_key, supabase_service_key]):
        print("\n❌ Missing required Supabase environment variables")
        return False
    
    try:
        # Test REST API connection
        print("\n🔗 Testing Supabase REST API...")
        
        headers = {
            'apikey': supabase_anon_key,
            'Authorization': f'Bearer {supabase_anon_key}',
            'Content-Type': 'application/json'
        }
        
        # Test database connection by counting user profiles
        url = f"{supabase_url}/rest/v1/user_profiles"
        headers['Prefer'] = 'count=exact'
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '0').split('/')[-1]
            print(f"✅ Database connection successful! Found {count} user profiles")
        else:
            print(f"❌ Database connection failed: {response.status_code} - {response.text}")
            return False
        
        # Test auth API
        print("🔐 Testing Supabase Auth API...")
        auth_url = f"{supabase_url}/auth/v1/settings"
        
        auth_response = requests.get(auth_url, headers=headers)
        
        if auth_response.status_code == 200:
            print("✅ Auth API connection successful")
        else:
            print(f"⚠️ Auth API test: {auth_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ HTTP Supabase test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_http_supabase()
    if success:
        print("\n🎉 HTTP Supabase is ready!")
        print("You can now run the main server with: python explain_with_grok.py --server")
    else:
        print("\n🔧 Fix the issues above before proceeding")