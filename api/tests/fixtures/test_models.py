"""
Simplified test fixtures for I18n testing.
"""
from typing import Dict, Any
from unittest.mock import Mock
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.serializers import Serializer

from api.i18n import I18nViewMixin, I18nSerializerMixin


class TestI18nView(I18nViewMixin, GenericViewSet):
    """Simple test view for I18n testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required DRF attributes
        self.format_kwarg = None
        self.action = None
        self.basename = 'test'
    
    def test_action(self, request: Request) -> Response:
        """Test action that returns language info."""
        return Response({
            'language': getattr(request, '_language', None),
            'message': 'Test message'
        }, status=status.HTTP_200_OK)


class TestI18nSerializer(I18nSerializerMixin, Serializer):
    """Simple test serializer for I18n testing."""
    
    def __init__(self, *args, **kwargs):
        self.activation_log = []  # Track language activations
        super().__init__(*args, **kwargs)
    
    def activate_language(self, language: str) -> str:
        """Override to track activations."""
        actual_language = super().activate_language(language)
        self.activation_log.append(actual_language)
        return actual_language


def create_mock_request(headers: Dict[str, str] = None, language: str = None) -> Mock:
    """Create a mock request with headers."""
    request = Mock()
    request.headers = headers or {}
    
    if language:
        request._language = language
        
    return request


def create_mock_context(language: str = None) -> Dict[str, Any]:
    """Create a mock serializer context."""
    context = {}
    if language:
        context['language'] = language
    return context
