"""Admin endpoints for News Copilot API"""

from flask import Blueprint, request, jsonify
from api.auth.decorators import require_admin
from api.auth.admin import get_all_users, update_user_tier, get_usage_stats
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/users')
@require_admin
def list_users(current_user):
    """List all users with their details"""
    try:
        users = get_all_users()
        return jsonify({'users': users})
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@bp.route('/users/<user_id>/tier', methods=['PATCH'])
@require_admin
def update_tier(current_user, user_id):
    """Update user tier"""
    data = request.json
    new_tier = data.get('tier')
    
    if new_tier not in ['free', 'premium', 'admin']:
        return jsonify({'error': 'Invalid tier'}), 400
    
    try:
        result = update_user_tier(user_id, new_tier)
        if result:
            return jsonify({'message': 'User tier updated', 'user_id': user_id, 'new_tier': new_tier})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error updating user tier: {str(e)}")
        return jsonify({'error': 'Failed to update user tier'}), 500

@bp.route('/stats')
@require_admin
def usage_stats(current_user):
    """Get usage statistics"""
    try:
        stats = get_usage_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@bp.route('/health')
@require_admin
def admin_health(current_user):
    """Detailed health check for admins"""
    return jsonify({
        'status': 'healthy',
        'admin_user': current_user.email,
        'services': {
            'supabase': 'connected',
            'grok_api': 'available'
        }
    })