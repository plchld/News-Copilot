# api/simple_auth.py
# Simplified auth system without Redis dependency for Vercel

import os
import jwt
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Tuple

# Use SQLite for both user data and rate limiting
from api.models import get_user, log_usage, UsageLog

# JWT secret
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

class UserTier:
    FREE = 'free'
    PRO = 'pro'
    PREMIUM = 'premium'
    BYOK = 'byok'

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
        'price': 8.99
    },
    UserTier.PREMIUM: {
        'basic_analysis': 150,
        'deep_analysis': 30,
        'price': 19.99
    },
    UserTier.BYOK: {
        'basic_analysis': float('inf'),
        'deep_analysis': float('inf'),
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

def get_monthly_usage(email: str, analysis_type: str) -> int:
    """Get usage count for current month from database"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM usage_logs 
        WHERE user_email = ? 
        AND analysis_type = ?
        AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
    ''', (email, analysis_type))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

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
            
            # Get user's custom API key if BYOK
            user = get_user(email)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Update tier from database (in case it changed)
            tier = user.tier
            
            # Check rate limit
            current_usage = get_monthly_usage(email, analysis_type)
            limit = TIER_LIMITS[tier].get(analysis_type, 0)
            
            if limit != float('inf') and current_usage >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'used': current_usage,
                    'limit': limit,
                    'tier': tier,
                    'upgrade_url': 'https://news-copilot.vercel.app/pricing'
                }), 429
            
            # Add user info to request
            request.user = {
                'email': email,
                'tier': tier,
                'api_key': user.api_key if tier == UserTier.BYOK else None
            }
            
            # Get the response first
            response = f(*args, **kwargs)
            
            # Log usage if successful
            if isinstance(response, tuple) and response[1] == 200:
                # Estimate token usage (simplified)
                tokens_used = 4000 if analysis_type == 'basic_analysis' else 6000
                cost_usd = 0.08 if analysis_type == 'basic_analysis' else 0.15
                
                log = UsageLog(
                    user_email=email,
                    analysis_type=analysis_type,
                    article_url=request.args.get('url', ''),
                    tokens_used=tokens_used,
                    cost_usd=cost_usd
                )
                log_usage(log)
            
            return response
            
        return decorated_function
    return decorator

def get_usage_stats(email: str) -> Dict:
    """Get current usage statistics for user"""
    stats = {
        'basic_analysis': get_monthly_usage(email, 'basic_analysis'),
        'deep_analysis': get_monthly_usage(email, 'deep_analysis')
    }
    return stats