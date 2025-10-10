"""
Internal API Authentication - Secure key based authentication for internal services
"""
from django.conf import settings
from rest_framework import authentication, exceptions


class InternalAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API key authentication for internal services.
    Clients should authenticate by passing the API key in the "X-Internal-API-Key" header.
    
    Usage:
    curl -H "X-Internal-API-Key: your-secret-key-here" http://localhost:8000/api/v3/internal/mapper/clubs/
    
    If authentication fails, raises AuthenticationFailed which results in 403 Forbidden.
    If authentication succeeds, the request is allowed to proceed.
    """
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_INTERNAL_API_KEY')
        
        if not api_key:
            raise exceptions.AuthenticationFailed('Missing X-Internal-API-Key header')
            
        expected_key = getattr(settings, 'INTERNAL_API_SECRET_KEY', None)
        
        if not expected_key:
            raise exceptions.AuthenticationFailed('Internal API key not configured on server')
            
        if api_key != expected_key:
            raise exceptions.AuthenticationFailed('Invalid internal API key')
            
        return None
