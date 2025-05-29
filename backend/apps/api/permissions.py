"""
Custom permissions for API endpoints
"""
import os
from rest_framework.permissions import BasePermission, IsAuthenticated
from django.conf import settings


class IsAuthenticatedOrOptional(BasePermission):
    """
    Permission class that allows access if user is authenticated OR if AUTH_REQUIRED is False
    """
    
    def has_permission(self, request, view):
        # Check if authentication is required
        auth_required = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'
        
        # If authentication is not required, allow access
        if not auth_required:
            return True
        
        # Otherwise, require authentication
        return IsAuthenticated().has_permission(request, view)


class NoAuthRequiredPermission(BasePermission):
    """
    Permission class that only allows access if AUTH_REQUIRED is False
    """
    
    def has_permission(self, request, view):
        auth_required = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'
        return not auth_required 