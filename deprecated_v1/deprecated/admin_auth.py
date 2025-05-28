# api/admin_auth.py
# Admin account management and authentication

import os
import hashlib
import secrets
from flask import Blueprint, request, jsonify
from api.models import get_db_connection
import psycopg2.extras
from datetime import datetime

admin_auth_bp = Blueprint('admin_auth', __name__)

# Your admin credentials (set these in environment variables)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'your-email@example.com')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')  # We'll generate this

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hash_hex = stored_hash.split(':')
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex() == hash_hex
    except:
        return False

def setup_admin_account(email: str, password: str):
    """Set up your admin account in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        # Insert or update admin user
        cursor.execute('''
            INSERT INTO users (email, tier, email_verified, is_admin, created_at)
            VALUES (%s, %s, true, true, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO UPDATE SET
                tier = 'admin',
                email_verified = true,
                is_admin = true
        ''', (email, 'admin'))
        
        # Store admin password hash separately (more secure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_credentials (
                email VARCHAR(255) PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO admin_credentials (email, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                updated_at = CURRENT_TIMESTAMP
        ''', (email, password_hash))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Admin account created for {email}")
        print(f"🔐 Password hash: {password_hash}")
        print("💡 Set ADMIN_PASSWORD_HASH environment variable to this hash")
        
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ Failed to create admin account: {e}")
        return False

@admin_auth_bp.route('/api/admin/setup', methods=['POST'])
def setup_admin():
    """One-time admin setup endpoint (disable after use)"""
    
    # Security: Only allow setup if no admin exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = true')
    admin_count = cursor.fetchone()[0]
    conn.close()
    
    if admin_count > 0:
        return jsonify({'error': 'Admin already exists'}), 403
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    if setup_admin_account(email, password):
        return jsonify({'message': 'Admin account created successfully'})
    else:
        return jsonify({'error': 'Failed to create admin account'}), 500

@admin_auth_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Verify admin credentials
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Check if user is admin
        cursor.execute('''
            SELECT u.email, u.is_admin, ac.password_hash
            FROM users u
            LEFT JOIN admin_credentials ac ON u.email = ac.email
            WHERE u.email = %s AND u.is_admin = true
        ''', (email,))
        
        admin = cursor.fetchone()
        conn.close()
        
        if not admin or not admin['password_hash']:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not verify_password(password, admin['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate admin token (longer expiry)
        from api.simple_auth import generate_token
        token = generate_token(email, 'admin')
        
        return jsonify({
            'token': token,
            'email': email,
            'role': 'admin'
        })
        
    except Exception as e:
        conn.close()
        print(f"Admin login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@admin_auth_bp.route('/api/admin/profile', methods=['GET'])
def admin_profile():
    """Get admin profile info"""
    from api.simple_auth import verify_token
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing token'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload or payload.get('tier') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get admin stats
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as total_logs FROM usage_logs WHERE DATE(created_at) = CURRENT_DATE')
        today_usage = cursor.fetchone()['total_logs']
        
        cursor.execute('SELECT SUM(cost_usd) as total_cost FROM usage_logs WHERE DATE(created_at) >= DATE_TRUNC(\'month\', CURRENT_DATE)')
        monthly_cost = cursor.fetchone()['total_cost'] or 0
        
        conn.close()
        
        return jsonify({
            'email': payload['email'],
            'role': 'admin',
            'stats': {
                'total_users': total_users,
                'today_usage': today_usage,
                'monthly_cost': float(monthly_cost)
            }
        })
        
    except Exception as e:
        conn.close()
        print(f"Admin profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

def generate_admin_password_hash(password: str):
    """Helper function to generate password hash for environment variable"""
    return hash_password(password)

if __name__ == "__main__":
    # Generate password hash for your admin account
    print("🔐 Admin Password Hash Generator")
    print("Use this to set ADMIN_PASSWORD_HASH environment variable")
    print("-" * 50)
    
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    hash_value = generate_admin_password_hash(password)
    print(f"\nPassword hash: {hash_value}")
    print(f"\nSet environment variable:")
    print(f"ADMIN_EMAIL={email}")
    print(f"ADMIN_PASSWORD_HASH={hash_value}")