#!/usr/bin/env python3
"""
Setup test environment for News Copilot
Creates test database and initializes tables
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from api.models import init_db

def setup_local_test_db():
    """Setup local PostgreSQL test database"""
    print("🔧 Setting up local test database...")
    
    # For local testing, you can use a local PostgreSQL instance
    # or use the same Neon database URL from Vercel
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("💡 Either:")
        print("   1. Set DATABASE_URL to your Neon database URL")
        print("   2. Set up a local PostgreSQL instance")
        return False
    
    try:
        # Test connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        conn.close()
        
        # Initialize database tables
        init_db()
        print("✅ Database tables initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'XAI_API_KEY',
        'DATABASE_URL',
        'JWT_SECRET',
        'ADMIN_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n💡 Create a .env file with:")
        for var in missing_vars:
            if var == 'XAI_API_KEY':
                print(f"   {var}=your_grok_api_key_here")
            elif var == 'DATABASE_URL':
                print(f"   {var}=your_neon_postgres_url_here")
            elif var == 'JWT_SECRET':
                print(f"   {var}=your_jwt_secret_key_here")
            elif var == 'ADMIN_KEY':
                print(f"   {var}=your_admin_secret_key_here")
        return False
    
    return True

def test_api_endpoints():
    """Test that the API endpoints are accessible"""
    print("🌐 Testing API endpoints...")
    
    import requests
    
    base_url = "http://localhost:8080"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
        # Test registration endpoint (without actually registering)
        response = requests.post(f"{base_url}/api/auth/register", 
                               json={}, timeout=5)
        # Should get 400 (bad request) which means endpoint is working
        if response.status_code in [400, 422]:
            print("✅ Registration endpoint accessible")
        else:
            print(f"⚠️ Registration endpoint returned: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to localhost:8080")
        print("💡 Start the backend server with: python explain_with_grok.py --server")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run all setup checks"""
    print("🧪 News Copilot Test Environment Setup")
    print("=" * 50)
    
    # Check environment variables
    if not check_environment():
        return
    
    # Setup database
    if not setup_local_test_db():
        return
    
    # Test API endpoints
    if not test_api_endpoints():
        print("\n💡 Start the backend server first:")
        print("   python explain_with_grok.py --server")
        return
    
    print("\n" + "=" * 50)
    print("🎉 Test environment setup complete!")
    print("=" * 50)
    print("\n📝 Next steps:")
    print("1. Run the test suite: python test_auth_system.py")
    print("2. Load the Chrome extension and test on a Greek news site")
    print("3. Open test_extension.html for interactive testing")

if __name__ == "__main__":
    main()