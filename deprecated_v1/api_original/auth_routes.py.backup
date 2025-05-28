# api/auth_routes.py
# Authentication and subscription endpoints

from flask import Blueprint, request, jsonify
from api.auth import generate_user_token, get_usage_stats, UserTier, TIER_LIMITS
from api.models import create_user, get_user, update_user_tier, User
from api.email_verification import create_verification_token, send_verification_email, is_email_verified
import os

auth_bp = Blueprint('auth', __name__)

# Demo mode for testing - in production, implement proper email verification
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with email"""
    data = request.json
    email = data.get('email')
    api_key = data.get('api_key')  # Optional BYOK
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Check if user exists
    existing_user = get_user(email)
    if existing_user:
        # If user exists but not verified, send new verification email
        if not is_email_verified(email) and not DEMO_MODE:
            verification_token = create_verification_token(email)
            if verification_token:
                send_verification_email(email, verification_token)
            return jsonify({
                'message': 'Verification email sent',
                'email_verified': False
            }), 200
        
        # Return existing user token
        token = generate_user_token(existing_user.email, existing_user.tier)
        return jsonify({
            'token': token,
            'user': {
                'email': existing_user.email,
                'tier': existing_user.tier,
                'email_verified': is_email_verified(email)
            },
            'usage': get_usage_stats(email)
        })
    
    # Determine tier based on API key
    tier = UserTier.BYOK if api_key else UserTier.FREE
    
    # Create new user
    user = User(email=email, tier=tier, api_key=api_key if api_key else None)
    if create_user(user):
        
        # Send verification email (unless demo mode or BYOK)
        if not DEMO_MODE and not api_key:
            verification_token = create_verification_token(email)
            if verification_token:
                send_verification_email(email, verification_token)
                return jsonify({
                    'message': 'Registration successful! Please check your email for verification.',
                    'email_verified': False
                }), 201
        
        # Demo mode or BYOK - return token immediately
        token = generate_user_token(email, tier)
        return jsonify({
            'token': token,
            'user': {
                'email': email,
                'tier': tier,
                'email_verified': DEMO_MODE or bool(api_key)
            },
            'usage': {'basic_analysis': 0, 'deep_analysis': 0}
        })
    
    return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login with email"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    user = get_user(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    token = generate_user_token(user.email, user.tier)
    return jsonify({
        'token': token,
        'tier': user.tier,
        'usage': get_usage_stats(email)
    })

@auth_bp.route('/api/auth/usage', methods=['GET'])
def usage():
    """Get current usage stats"""
    # Get email from token
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing token'}), 401
    
    # In production, decode token properly
    # For now, simplified demo
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    user = get_user(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    stats = get_usage_stats(email)
    limits = TIER_LIMITS[user.tier]
    
    return jsonify({
        'tier': user.tier,
        'usage': stats,
        'limits': {
            'basic_analysis': limits['basic_analysis'],
            'deep_analysis': limits['deep_analysis']
        },
        'price': limits['price']
    })

@auth_bp.route('/api/auth/tiers', methods=['GET'])
def tiers():
    """Get available subscription tiers"""
    return jsonify({
        'tiers': [
            {
                'id': UserTier.FREE,
                'name': 'Free',
                'price': 0,
                'limits': {
                    'basic_analysis': TIER_LIMITS[UserTier.FREE]['basic_analysis'],
                    'deep_analysis': TIER_LIMITS[UserTier.FREE]['deep_analysis']
                },
                'features': [
                    '10 article analyses per month',
                    'Basic jargon explanations',
                    'Alternative viewpoints'
                ]
            },
            {
                'id': UserTier.PRO,
                'name': 'Pro',
                'price': 4.99,
                'limits': {
                    'basic_analysis': TIER_LIMITS[UserTier.PRO]['basic_analysis'],
                    'deep_analysis': TIER_LIMITS[UserTier.PRO]['deep_analysis']
                },
                'features': [
                    '100 article analyses per month',
                    '20 deep analyses (fact-check, bias, etc)',
                    'Priority processing',
                    'Email support'
                ]
            },
            {
                'id': UserTier.PREMIUM,
                'name': 'Premium',
                'price': 9.99,
                'limits': {
                    'basic_analysis': TIER_LIMITS[UserTier.PREMIUM]['basic_analysis'],
                    'deep_analysis': TIER_LIMITS[UserTier.PREMIUM]['deep_analysis']
                },
                'features': [
                    'Unlimited article analyses*',
                    '50 deep analyses per month',
                    'Priority processing',
                    'Custom API webhook',
                    'Priority support'
                ]
            },
            {
                'id': UserTier.BYOK,
                'name': 'Bring Your Own Key',
                'price': 0,
                'limits': {
                    'basic_analysis': 'unlimited',
                    'deep_analysis': 'unlimited'
                },
                'features': [
                    'Use your own Grok API key',
                    'Unlimited analyses',
                    'Pay X.AI directly',
                    'Full API access'
                ]
            }
        ]
    })

@auth_bp.route('/api/auth/set-api-key', methods=['POST'])
def set_api_key():
    """Set custom API key for BYOK users"""
    data = request.json
    email = data.get('email')
    api_key = data.get('api_key')
    
    if not email or not api_key:
        return jsonify({'error': 'Email and API key required'}), 400
    
    user = get_user(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update user to BYOK tier
    user.tier = UserTier.BYOK
    user.api_key = api_key
    
    # In production, validate the API key with X.AI
    # For now, just update the user
    update_user_tier(email, UserTier.BYOK)
    
    # Store API key in Redis for fast access
    from api.auth import set_user_api_key
    set_user_api_key(email, api_key)
    
    token = generate_user_token(email, UserTier.BYOK)
    return jsonify({
        'success': True,
        'token': token,
        'tier': UserTier.BYOK
    })