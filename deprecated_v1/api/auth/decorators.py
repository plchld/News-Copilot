"""Authentication decorators for Flask routes"""

from functools import wraps
from flask import request, jsonify
from .supabase import get_user_by_token
from .models import User
import logging

logger = logging.getLogger(__name__)

def optional_auth(f):
    """Allow both authenticated and anonymous requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        current_user = None
        
        if token:
            try:
                current_user = get_user_by_token(token)
            except Exception as e:
                logger.warning(f"Optional auth token validation failed: {str(e)}")
                # Continue without auth for optional endpoints
        
        return f(*args, current_user=current_user, **kwargs)
    return decorated_function

def require_auth(f):
    """Require valid authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            current_user = get_user_by_token(token)
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
                
            return f(*args, current_user=current_user, **kwargs)
        except Exception as e:
            logger.error(f"Auth verification failed: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
            
    return decorated_function

def require_admin(f):
    """Require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        try:
            current_user = get_user_by_token(token)
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
            
            if current_user.tier != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
                
            return f(*args, current_user=current_user, **kwargs)
        except Exception as e:
            logger.error(f"Admin auth verification failed: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
            
    return decorated_function