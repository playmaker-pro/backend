"""
Test fixtures and utilities for I18n testing.
"""
from typing import Dict, Any
from unittest.mock import Mock
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from api.i18n import I18nViewMixin, I18nSerializerMixin


class MockModelMeta:
    """Mock meta class for Django model compatibility."""
    def __init__(self):
        from django.db.models.fields import Field, CharField
        
        # Create actual field objects
        name_field = CharField(max_length=100)
        name_field.name = 'name'
        name_field.attname = 'name'
        name_field.column = 'name'
        name_field.serialize = True
        name_field.remote_field = None
        
        desc_field = CharField(max_length=255)
        desc_field.name = 'description'
        desc_field.attname = 'description'
        desc_field.column = 'description'
        desc_field.serialize = True
        desc_field.remote_field = None
        
        self.fields = [name_field, desc_field]
        self.many_to_many = []  # No many-to-many fields
        self.related_objects = []  # No related objects
        self.parents = {}  # No parent models
        self.unique_together = []  # No unique together constraints
        
        self.concrete_model = None
        self.app_label = 'test'
        self.model_name = 'mockmodel'
        self.verbose_name = 'Mock Model'
        self.verbose_name_plural = 'Mock Models'
        self.abstract = False
        self.proxy = False
        self.swapped = False
        
        # Add pk field to satisfy model_meta.get_field_info
        self.pk = Field()
        self.pk.name = 'id'
        self.pk.attname = 'id'
        self.pk.column = 'id'
        self.pk.primary_key = True
    
    def get_field(self, field_name):
        """Get a field by name."""
        for field in self.fields:
            if field.name == field_name:
                return field
        from django.core.exceptions import FieldDoesNotExist
        raise FieldDoesNotExist(f"Field '{field_name}' does not exist")
    
    @property
    def label(self):
        return f'{self.app_label}.{self.model_name}'


class MockModel:
    """Mock model for testing serializers."""
    def __init__(self, name="Test Name", description="Test Description"):
        self.name = name
        self.description = description
        self.pk = 1
        self.id = 1
    
    _meta = MockModelMeta()
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        pass
        
    def delete(self, *args, **kwargs):
        pass

# Set the concrete_model after the class is defined
MockModel._meta.concrete_model = MockModel


class MockI18nView(I18nViewMixin, GenericViewSet):
    """Mock view using I18nViewMixin."""
    
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
    
    def get_serializer_context(self) -> Dict[str, Any]:
        """Override to test context passing."""
        return super().get_serializer_context()


class MockI18nSerializer(I18nSerializerMixin, ModelSerializer):
    """Mock serializer using I18nSerializerMixin."""
    
    class Meta:
        model = MockModel
        fields = ['name', 'description']
        validators = []  # Disable uniqueness validation to avoid model introspection
    
    def __init__(self, *args, **kwargs):
        self.activation_log = []  # Track language activations for testing
        super().__init__(*args, **kwargs)
    
    def activate_language(self, language: str) -> str:
        """Override to track activations."""
        # Call the real method first to get the actual activated language
        actual_language = super().activate_language(language)
        # Log the actual activated language (which may be different due to fallbacks)
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
