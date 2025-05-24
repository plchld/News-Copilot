#!/usr/bin/env python3
"""
Simple test for Supabase authentication
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🧪 Testing Supabase Connection")
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
        from supabase import create_client
        print("\n✅ Supabase library imported successfully")
        
        # Test client creation
        print("🔗 Creating Supabase client...")
        client = create_client(supabase_url, supabase_anon_key)
        print("✅ Supabase client created successfully")
        
        # Test database connection
        print("🗄️ Testing database connection...")
        response = client.table('user_profiles').select('count', count='exact').execute()
        user_count = response.count
        print(f"✅ Database connection successful! Found {user_count} user profiles")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    if success:
        print("\n🎉 Supabase is ready!")
        print("You can now run the main server with: python explain_with_grok.py --server")
    else:
        print("\n🔧 Fix the issues above before proceeding")