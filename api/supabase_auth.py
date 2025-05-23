# api/supabase_auth.py
# Supabase authentication and user management

import os
from supabase import create_client, Client
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, Dict
import json

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # For admin operations

# Initialize Supabase clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

supabase_auth_bp = Blueprint('supabase_auth', __name__)

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

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile from Supabase"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

def create_user_profile(user_id: str, email: str, tier: str = UserTier.FREE, api_key: str = None) -> bool:
    """Create user profile in Supabase"""
    if not supabase:
        return False
    
    try:
        profile_data = {
            'user_id': user_id,
            'email': email,
            'tier': tier,
            'api_key': api_key,
            'created_at': datetime.utcnow().isoformat(),
            'email_verified': True  # Supabase handles email verification
        }
        
        response = supabase.table('user_profiles').insert(profile_data).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error creating user profile: {e}")
        return False

def get_usage_stats(user_id: str) -> Dict:
    """Get monthly usage statistics for user"""
    if not supabase:
        return {'basic_analysis': 0, 'deep_analysis': 0}
    
    try:
        # Get current month's usage
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        response = supabase.table('usage_logs').select('analysis_type').eq('user_id', user_id).gte('created_at', start_of_month.isoformat()).execute()
        
        usage = {'basic_analysis': 0, 'deep_analysis': 0}
        for log in response.data:
            analysis_type = log.get('analysis_type', 'basic_analysis')
            if analysis_type in ['jargon', 'viewpoints']:
                usage['basic_analysis'] += 1
            else:
                usage['deep_analysis'] += 1
        
        return usage
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        return {'basic_analysis': 0, 'deep_analysis': 0}

def log_usage(user_id: str, analysis_type: str, article_url: str = None, tokens_used: int = 0, cost_usd: float = 0):
    """Log API usage to Supabase"""
    if not supabase:
        return
    
    try:
        usage_data = {
            'user_id': user_id,
            'analysis_type': analysis_type,
            'article_url': article_url,
            'tokens_used': tokens_used,
            'cost_usd': cost_usd,
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('usage_logs').insert(usage_data).execute()
    except Exception as e:
        print(f"Error logging usage: {e}")

def verify_supabase_token(token: str) -> Optional[Dict]:
    """Verify Supabase JWT token"""
    if not supabase:
        return None
    
    try:
        # Set the auth token
        supabase.auth.set_session(access_token=token, refresh_token="")
        
        # Get user info
        user = supabase.auth.get_user(token)
        if user and user.user:
            return {
                'user_id': user.user.id,
                'email': user.user.email,
                'email_verified': user.user.email_confirmed_at is not None
            }
    except Exception as e:
        print(f"Error verifying token: {e}")
    
    return None

def require_supabase_auth(analysis_type: str = 'basic_analysis'):
    """Decorator to require Supabase authentication and check rate limits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing authentication token'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token with Supabase
            user_data = verify_supabase_token(token)
            if not user_data:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Get user profile
            profile = get_user_profile(user_data['user_id'])
            if not profile:
                # Create profile if it doesn't exist (first time user)
                create_user_profile(user_data['user_id'], user_data['email'])
                profile = get_user_profile(user_data['user_id'])
            
            # Check if email is verified (unless BYOK)
            if not user_data['email_verified'] and profile['tier'] != UserTier.BYOK:
                return jsonify({'error': 'Email not verified'}), 403
            
            # Check rate limits (unless BYOK or admin)
            if profile['tier'] not in [UserTier.BYOK, UserTier.ADMIN]:
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
            request.user_tier = profile['tier']
            request.user_api_key = profile.get('api_key')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# API Endpoints

@supabase_auth_bp.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """Get user profile and usage stats"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authentication token'}), 401
    
    token = auth_header.split(' ')[1]
    user_data = verify_supabase_token(token)
    
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

@supabase_auth_bp.route('/api/auth/update-api-key', methods=['POST'])
def update_api_key():
    """Update user's API key for BYOK"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authentication token'}), 401
    
    token = auth_header.split(' ')[1]
    user_data = verify_supabase_token(token)
    
    if not user_data:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    # Update user profile
    new_tier = UserTier.BYOK if api_key else UserTier.FREE
    
    try:
        supabase.table('user_profiles').update({
            'api_key': api_key if api_key else None,
            'tier': new_tier,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_data['user_id']).execute()
        
        return jsonify({
            'message': 'API key updated successfully',
            'tier': new_tier
        })
    except Exception as e:
        print(f"Error updating API key: {e}")
        return jsonify({'error': 'Failed to update API key'}), 500

@supabase_auth_bp.route('/api/auth/magic-link', methods=['POST'])
def send_magic_link():
    """Send magic link for authentication (handled by Supabase)"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    try:
        # Supabase handles magic link sending
        response = supabase.auth.sign_in_with_otp({
            'email': email,
            'options': {
                'redirect_to': f"{os.getenv('BASE_URL', 'http://localhost:8080')}/auth/callback"
            }
        })
        
        return jsonify({
            'message': 'Magic link sent to your email',
            'email': email
        })
    except Exception as e:
        print(f"Error sending magic link: {e}")
        return jsonify({'error': 'Failed to send magic link'}), 500

@supabase_auth_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Handle Supabase auth callback"""
    # This will be handled by the frontend (Chrome extension)
    return '''
    <html>
    <body>
        <h1>Authentication Successful!</h1>
        <p>You can now close this tab and return to the extension.</p>
        <script>
            // Notify parent window if opened from extension
            if (window.opener) {
                window.opener.postMessage({type: 'AUTH_SUCCESS'}, '*');
                window.close();
            }
        </script>
    </body>
    </html>
    '''