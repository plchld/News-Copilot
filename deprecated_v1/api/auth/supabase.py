"""Supabase client and authentication functions"""

import os
from supabase import create_client, Client
from .models import User
from datetime import datetime
import logging
from api.config import config

logger = logging.getLogger(__name__)

# Initialize Supabase client only if auth is required
supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get Supabase client, initializing if needed"""
    global supabase_client
    if supabase_client is None and config.AUTH_REQUIRED:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase configuration required when AUTH_REQUIRED=true")
        supabase_client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_KEY
        )
    return supabase_client

def verify_token(token: str) -> dict:
    """Verify JWT token with Supabase"""
    if not config.AUTH_REQUIRED:
        return None
    
    client = get_supabase_client()
    if not client:
        return None
        
    try:
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                'id': user_response.user.id,
                'email': user_response.user.email
            }
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
    return None

def get_user_by_token(token: str) -> User:
    """Get full user object by token"""
    auth_user = verify_token(token)
    if not auth_user:
        return None
    
    client = get_supabase_client()
    if not client:
        return None
        
    try:
        # Get user details from database
        response = client.table('users').select('*').eq('id', auth_user['id']).single().execute()
        
        if response.data:
            user_data = response.data
            return User(
                id=user_data['id'],
                email=user_data['email'],
                tier=user_data.get('tier', 'free'),
                api_key=user_data.get('api_key'),
                analyses_this_month=user_data.get('analyses_this_month', 0),
                created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else None
            )
    except Exception as e:
        logger.error(f"Failed to get user data: {str(e)}")
    
    # Return basic user if database lookup fails
    return User(
        id=auth_user['id'],
        email=auth_user['email'],
        tier='free'
    )

def create_magic_link(email: str, redirect_to: str = None) -> dict:
    """Create magic link for email authentication"""
    if not config.AUTH_REQUIRED:
        return {'error': 'Authentication not enabled'}
        
    client = get_supabase_client()
    if not client:
        return {'error': 'Supabase client not available'}
        
    try:
        # Use the configured redirect URL or default
        if not redirect_to:
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            redirect_to = f"{base_url}/auth/callback"
        
        response = client.auth.sign_in_with_otp({
            'email': email,
            'options': {
                'email_redirect_to': redirect_to
            }
        })
        
        if response:
            return {'success': True, 'message': 'Magic link sent'}
        else:
            return {'error': 'Failed to send magic link'}
            
    except Exception as e:
        logger.error(f"Magic link creation failed: {str(e)}")
        return {'error': str(e)}

def update_user_usage(user_id: str, increment: int = 1):
    """Update user's monthly usage count"""
    if not config.AUTH_REQUIRED:
        return
        
    client = get_supabase_client()
    if not client:
        return
        
    try:
        # Get current usage
        response = client.table('users').select('analyses_this_month').eq('id', user_id).single().execute()
        current_usage = response.data.get('analyses_this_month', 0) if response.data else 0
        
        # Update usage
        client.table('users').update({
            'analyses_this_month': current_usage + increment
        }).eq('id', user_id).execute()
        
    except Exception as e:
        logger.error(f"Failed to update user usage: {str(e)}")