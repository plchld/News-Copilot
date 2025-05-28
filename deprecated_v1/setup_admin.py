#!/usr/bin/env python3
"""
Setup script for News Copilot admin account
Run this once to create your admin account
"""

import os
from dotenv import load_dotenv
from api.admin_auth import setup_admin_account, generate_admin_password_hash

load_dotenv()

def main():
    print("🔐 News Copilot Admin Setup")
    print("=" * 40)
    
    # Check if admin already exists
    try:
        from api.models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = true')
        admin_count = cursor.fetchone()[0]
        conn.close()
        
        if admin_count > 0:
            print("❌ Admin account already exists!")
            print("Use the existing admin login credentials.")
            return
            
    except Exception as e:
        print(f"⚠️ Database check failed: {e}")
        print("Continuing with setup...")
    
    print("Creating your admin account...")
    print()
    
    # Get admin details
    email = input("Admin email: ").strip()
    if not email:
        print("❌ Email is required")
        return
    
    password = input("Admin password (min 8 chars): ").strip()
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords don't match")
        return
    
    print()
    print("Setting up admin account...")
    
    # Create admin account
    if setup_admin_account(email, password):
        password_hash = generate_admin_password_hash(password)
        
        print()
        print("✅ Admin account created successfully!")
        print()
        print("🔧 Add these environment variables to Vercel:")
        print(f"ADMIN_EMAIL={email}")
        print(f"ADMIN_PASSWORD_HASH={password_hash}")
        print()
        print("📝 Save these credentials securely:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print()
        print("🌐 Admin endpoints:")
        print("• POST /api/admin/login - Admin login")
        print("• GET /api/admin/profile - Admin profile")
        print("• GET /api/admin/users - User management")
        print("• GET /api/admin/usage-stats - Usage analytics")
        print("• GET /api/admin/export-emails - Export user emails")
        
    else:
        print("❌ Failed to create admin account")

if __name__ == "__main__":
    main()