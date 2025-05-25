# api/auth.py
# User authentication and rate limiting system

import os
import jwt
import redis
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Tuple

# Redis connection for rate limiting
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# JWT secret
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

class UserTier:
    FREE = 'free'
    PRO = 'pro'
    PREMIUM = 'premium'
    BYOK = 'byok'  # Bring Your Own Key

# Rate limits per tier (monthly)
TIER_LIMITS = {
    UserTier.FREE: {
        'basic_analysis': 10,
        'deep_analysis': 0,
        'price': 0
    },
    UserTier.PRO: {
        'basic_analysis': 50,
        'deep_analysis': 10,
        'price': 8.99  # EUR
    },
    UserTier.PREMIUM: {
        'basic_analysis': 150,
        'deep_analysis': 30,
        'price': 19.99  # EUR
    },
    UserTier.BYOK: {
        'basic_analysis': 999999,
        'deep_analysis': 999999,
        'price': 0
    }
}

def generate_user_token(email: str, tier: str = UserTier.FREE) -> str:
    """Generate JWT token for user"""
    payload = {
        'email': email,
        'tier': tier,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_id(email: str) -> str:
    """Generate consistent user ID from email"""
    return hashlib.sha256(email.encode()).hexdigest()[:16]

def get_usage_key(user_id: str, analysis_type: str) -> str:
    """Generate Redis key for usage tracking"""
    month = datetime.now().strftime('%Y-%m')
    return f"usage:{user_id}:{month}:{analysis_type}"

def check_rate_limit(email: str, tier: str, analysis_type: str) -> Tuple[bool, int, int]:
    """
    Check if user is within rate limits
    Returns: (allowed, used, limit)
    """
    user_id = get_user_id(email)
    usage_key = get_usage_key(user_id, analysis_type)
    
    # Get current usage
    current_usage = redis_client.get(usage_key)
    used = int(current_usage) if current_usage else 0
    
    # Get limit for tier
    limit = TIER_LIMITS[tier].get(analysis_type, 0)
    
    # Check if within limit
    allowed = used < limit if limit != 999999 else True
    
    return allowed, used, limit

def increment_usage(email: str, analysis_type: str) -> None:
    """Increment usage counter"""
    user_id = get_user_id(email)
    usage_key = get_usage_key(user_id, analysis_type)
    
    # Increment with expiry at end of month
    redis_client.incr(usage_key)
    
    # Set expiry to end of current month
    days_in_month = 31  # Simplified
    redis_client.expire(usage_key, days_in_month * 24 * 60 * 60)

def get_user_api_key(email: str) -> Optional[str]:
    """Get user's custom API key if BYOK tier"""
    user_id = get_user_id(email)
    key = f"api_key:{user_id}"
    return redis_client.get(key)

def set_user_api_key(email: str, api_key: str) -> None:
    """Store user's custom API key"""
    user_id = get_user_id(email)
    key = f"api_key:{user_id}"
    redis_client.set(key, api_key)

def require_auth(analysis_type: str = 'basic_analysis'):
    """Decorator to require authentication and check rate limits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing authentication token'}), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            email = payload['email']
            tier = payload.get('tier', UserTier.FREE)
            
            # Check rate limit
            allowed, used, limit = check_rate_limit(email, tier, analysis_type)
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'used': used,
                    'limit': limit,
                    'tier': tier,
                    'upgrade_url': 'https://news-copilot.vercel.app/pricing'
                }), 429
            
            # Add user info to request
            request.user = {
                'email': email,
                'tier': tier,
                'api_key': get_user_api_key(email) if tier == UserTier.BYOK else None
            }
            
            # Increment usage after successful request
            response = f(*args, **kwargs)
            if response[1] == 200:  # Only count successful requests
                increment_usage(email, analysis_type)
            
            return response
            
        return decorated_function
    return decorator

def get_usage_stats(email: str) -> Dict:
    """Get current usage statistics for user"""
    user_id = get_user_id(email)
    month = datetime.now().strftime('%Y-%m')
    
    stats = {}
    for analysis_type in ['basic_analysis', 'deep_analysis']:
        usage_key = f"usage:{user_id}:{month}:{analysis_type}"
        current_usage = redis_client.get(usage_key)
        stats[analysis_type] = int(current_usage) if current_usage else 0
    
    return stats