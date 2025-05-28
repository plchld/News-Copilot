"""Admin-specific authentication functions"""

from .supabase import supabase_client
import logging

logger = logging.getLogger(__name__)

def get_all_users():
    """Get all users for admin dashboard"""
    try:
        response = supabase_client.table('users').select('*').order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        return []

def update_user_tier(user_id: str, new_tier: str) -> bool:
    """Update user's subscription tier"""
    try:
        response = supabase_client.table('users').update({
            'tier': new_tier
        }).eq('id', user_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Failed to update user tier: {str(e)}")
        return False

def get_usage_stats():
    """Get overall usage statistics"""
    try:
        # Get user counts by tier
        users_response = supabase_client.table('users').select('tier').execute()
        users_data = users_response.data if users_response.data else []
        
        tier_counts = {'free': 0, 'premium': 0, 'admin': 0}
        for user in users_data:
            tier = user.get('tier', 'free')
            if tier in tier_counts:
                tier_counts[tier] += 1
        
        # Get total analyses this month
        analyses_response = supabase_client.table('users').select('analyses_this_month').execute()
        total_analyses = sum(user.get('analyses_this_month', 0) for user in (analyses_response.data or []))
        
        return {
            'total_users': len(users_data),
            'users_by_tier': tier_counts,
            'total_analyses_this_month': total_analyses
        }
    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        return {
            'error': 'Failed to fetch statistics',
            'total_users': 0,
            'users_by_tier': {'free': 0, 'premium': 0, 'admin': 0},
            'total_analyses_this_month': 0
        }