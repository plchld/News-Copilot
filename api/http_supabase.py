# api/http_supabase.py
# Simple HTTP-based Supabase client that avoids library compatibility issues

import os
import requests
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Optional, Dict

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

http_supabase_bp = Blueprint('http_supabase', __name__)

class UserTier:
    FREE = 'free'
    PRO = 'pro'
    PREMIUM = 'premium'
    BYOK = 'byok'
    ADMIN = 'admin'

# Tier limits (monthly)
TIER_LIMITS = {
    UserTier.FREE: {
        'basic_analysis': 10,
        'deep_analysis': 0,
        'price': 0
    },
    UserTier.PRO: {
        'basic_analysis': 50,
        'deep_analysis': 10,
        'price': 8.99
    },
    UserTier.PREMIUM: {
        'basic_analysis': 150,
        'deep_analysis': 30,
        'price': 24.99
    },
    UserTier.BYOK: {
        'basic_analysis': float('inf'),
        'deep_analysis': float('inf'),
        'price': 0
    }
}

def get_headers(use_service_key=False):
    """Get headers for Supabase REST API requests"""
    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

def verify_supabase_jwt(token: str) -> Optional[Dict]:
    """Verify Supabase JWT token"""
    try:
        # Decode without signature verification for now
        # In production, you'd verify with Supabase's public key
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'email_verified': payload.get('email_confirmed_at') is not None
        }
    except Exception as e:
        print(f"Error verifying JWT: {e}")
        return None

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile from Supabase via REST API"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles"
        params = {'user_id': f'eq.{user_id}', 'select': '*'}
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        else:
            print(f"Error getting user profile: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

def create_user_profile(user_id: str, email: str, tier: str = UserTier.FREE, api_key: str = None) -> bool:
    """Create user profile in Supabase via REST API"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles"
        
        profile_data = {
            'user_id': user_id,
            'email': email,
            'tier': tier,
            'api_key': api_key,
            'email_verified': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.post(url, headers=get_headers(use_service_key=True), json=profile_data)
        return response.status_code in [200, 201]
        
    except Exception as e:
        print(f"Error creating user profile: {e}")
        return False

def get_usage_stats(user_id: str) -> Dict:
    """Get monthly usage statistics for user"""
    try:
        # Get current month's usage
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        url = f"{SUPABASE_URL}/rest/v1/usage_logs"
        params = {
            'user_id': f'eq.{user_id}',
            'created_at': f'gte.{start_of_month.isoformat()}',
            'select': 'analysis_type'
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            logs = response.json()
            usage = {'basic_analysis': 0, 'deep_analysis': 0}
            
            for log in logs:
                analysis_type = log.get('analysis_type', 'basic_analysis')
                if analysis_type in ['jargon', 'viewpoints']:
                    usage['basic_analysis'] += 1
                else:
                    usage['deep_analysis'] += 1
            
            return usage
        else:
            return {'basic_analysis': 0, 'deep_analysis': 0}
            
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        return {'basic_analysis': 0, 'deep_analysis': 0}

def log_usage(user_id: str, analysis_type: str, article_url: str = None, tokens_used: int = 0, cost_usd: float = 0):
    """Log API usage to Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/usage_logs"
        
        usage_data = {
            'user_id': user_id,
            'analysis_type': analysis_type,
            'article_url': article_url,
            'tokens_used': tokens_used,
            'cost_usd': cost_usd,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = requests.post(url, headers=get_headers(use_service_key=True), json=usage_data)
        return response.status_code in [200, 201]
        
    except Exception as e:
        print(f"Error logging usage: {e}")
        return False

def require_http_supabase_auth(analysis_type: str = 'basic_analysis'):
    """Decorator to require Supabase authentication and check rate limits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing authentication token'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token
            user_data = verify_supabase_jwt(token)
            if not user_data:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Get user profile
            profile = get_user_profile(user_data['user_id'])
            if not profile:
                # Create profile if it doesn't exist (first time user)
                create_user_profile(user_data['user_id'], user_data['email'])
                profile = get_user_profile(user_data['user_id'])
            
            # Check rate limits (unless BYOK or admin)
            if profile and profile['tier'] not in [UserTier.BYOK, UserTier.ADMIN]:
                usage = get_usage_stats(user_data['user_id'])
                limits = TIER_LIMITS.get(profile['tier'], TIER_LIMITS[UserTier.FREE])
                
                if analysis_type == 'basic_analysis':
                    if usage['basic_analysis'] >= limits['basic_analysis']:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'usage': usage,
                            'limits': limits
                        }), 429
                else:  # deep_analysis
                    if usage['deep_analysis'] >= limits['deep_analysis']:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'usage': usage,
                            'limits': limits
                        }), 429
            
            # Add user info to request context
            request.user_id = user_data['user_id']
            request.user_email = user_data['email']
            request.user_tier = profile['tier'] if profile else UserTier.FREE
            request.user_api_key = profile.get('api_key') if profile else None
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# API Endpoints

@http_supabase_bp.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """Get user profile and usage stats"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authentication token'}), 401
    
    token = auth_header.split(' ')[1]
    user_data = verify_supabase_jwt(token)
    
    if not user_data:
        return jsonify({'error': 'Invalid token'}), 401
    
    profile = get_user_profile(user_data['user_id'])
    if not profile:
        # Create profile for new user
        create_user_profile(user_data['user_id'], user_data['email'])
        profile = get_user_profile(user_data['user_id'])
    
    usage = get_usage_stats(user_data['user_id'])
    limits = TIER_LIMITS.get(profile['tier'], TIER_LIMITS[UserTier.FREE])
    
    return jsonify({
        'user_id': user_data['user_id'],
        'email': profile['email'],
        'tier': profile['tier'],
        'email_verified': user_data['email_verified'],
        'usage_this_month': usage,
        'usage_limits': limits,
        'has_api_key': bool(profile.get('api_key'))
    })

@http_supabase_bp.route('/api/auth/update-api-key', methods=['POST'])
def update_api_key():
    """Update user's API key for BYOK"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authentication token'}), 401
    
    token = auth_header.split(' ')[1]
    user_data = verify_supabase_jwt(token)
    
    if not user_data:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    # Update user profile
    new_tier = UserTier.BYOK if api_key else UserTier.FREE
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles"
        params = {'user_id': f'eq.{user_data["user_id"]}'}
        
        update_data = {
            'api_key': api_key if api_key else None,
            'tier': new_tier,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.patch(url, headers=get_headers(use_service_key=True), params=params, json=update_data)
        
        if response.status_code == 200:
            return jsonify({
                'message': 'API key updated successfully',
                'tier': new_tier
            })
        else:
            return jsonify({'error': 'Failed to update API key'}), 500
            
    except Exception as e:
        print(f"Error updating API key: {e}")
        return jsonify({'error': 'Failed to update API key'}), 500

@http_supabase_bp.route('/api/auth/magic-link', methods=['POST'])
def send_magic_link():
    """Send magic link for authentication"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    try:
        # Send magic link via Supabase Auth API
        auth_url = f"{SUPABASE_URL}/auth/v1/magiclink"
        auth_data = {
            'email': email,
            'redirect_to': f"{os.getenv('BASE_URL', 'http://localhost:8080')}/auth/callback"
        }
        
        response = requests.post(auth_url, headers=get_headers(), json=auth_data)
        
        if response.status_code in [200, 201]:
            return jsonify({
                'message': 'Magic link sent to your email',
                'email': email
            })
        else:
            print(f"Magic link error: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to send magic link'}), 500
            
    except Exception as e:
        print(f"Error sending magic link: {e}")
        return jsonify({'error': 'Failed to send magic link'}), 500

@http_supabase_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Handle Supabase auth callback"""
    return '''
    <html>
    <body>
        <h1>Authentication Successful!</h1>
        <p>You can now close this tab and return to the extension.</p>
        <script>
            if (window.opener) {
                window.opener.postMessage({type: 'AUTH_SUCCESS'}, '*');
                window.close();
            }
        </script>
    </body>
    </html>
    '''