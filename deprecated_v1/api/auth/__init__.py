"""Authentication module for News Copilot"""

from .decorators import optional_auth, require_auth, require_admin
from .models import User
from .supabase import supabase_client, verify_token

__all__ = [
    'optional_auth', 
    'require_auth', 
    'require_admin',
    'User',
    'supabase_client',
    'verify_token'
]