"""Authentication endpoints for News Copilot API"""

from flask import Blueprint, request, jsonify
from api.auth.supabase import supabase_client, create_magic_link
from api.auth.decorators import require_auth
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    """Send magic link for email authentication"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        # Create magic link
        result = create_magic_link(email)
        
        if result.get('error'):
            return jsonify({'error': result['error']}), 400
            
        return jsonify({
            'message': 'Magic link sent to your email',
            'email': email
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Failed to send magic link'}), 500

@bp.route('/profile')
@require_auth
def profile(current_user):
    """Get user profile information"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'tier': current_user.tier,
        'usage': {
            'analyses_this_month': current_user.analyses_this_month,
            'limit': current_user.monthly_limit
        },
        'created_at': current_user.created_at.isoformat() if hasattr(current_user.created_at, 'isoformat') else str(current_user.created_at)
    })

@bp.route('/logout', methods=['POST'])
@require_auth
def logout(current_user):
    """Logout user (client-side token removal)"""
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify JWT token validity"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'}), 401
    
    try:
        user = supabase_client.auth.get_user(token)
        if user and user.user:
            return jsonify({
                'valid': True,
                'user': {
                    'id': user.user.id,
                    'email': user.user.email
                }
            })
        else:
            return jsonify({'valid': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

@bp.route('/callback')
def auth_callback():
    """Handle Supabase auth callback"""
    return '''
    <html>
    <body>
        <h1>Authentication Successful!</h1>
        <p>You can now close this tab and return to the application.</p>
        <script>
            if (window.opener) {
                window.opener.postMessage({type: 'AUTH_SUCCESS'}, '*');
                window.close();
            }
        </script>
    </body>
    </html>
    '''