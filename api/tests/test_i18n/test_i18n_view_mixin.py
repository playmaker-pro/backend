"""
Tests for I18nViewMixin functionality.
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from rest_framework.test import APITestCase
from rest_framework.request import Request
from rest_framework import status

from api.i18n import I18nViewMixin
from api.i18n_config import SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE
from ..fixtures.test_models import MockI18nView, create_mock_request


class I18nViewMixinTests(TestCase):
    """Test cases for I18nViewMixin."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.view = MockI18nView()
        self.view.request = None  # Will be set per test

    @patch.object(I18nViewMixin, 'activate_language')
    @patch.object(I18nViewMixin, 'get_request_language')
    def test_dispatch_calls_language_detection_and_activation(self, mock_get_lang, mock_activate):
        """Test that dispatch method calls language detection and activation."""
        # Setup mocks
        mock_get_lang.return_value = 'en'
        mock_activate.return_value = 'en'
        
        # Create a mock parent class dispatch method
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Create request
            django_request = self.factory.get('/')
            request = Request(django_request)
            
            # Call dispatch
            self.view.dispatch(request)
            
            # Verify language detection was called
            mock_get_lang.assert_called_once_with(request)
            
            # Verify language activation was called
            mock_activate.assert_called_once_with('en')
            
            # Verify super().dispatch was called
            mock_super_dispatch.assert_called_once()

    def test_dispatch_stores_language_in_request(self):
        """Test that dispatch stores language in request object."""
        # Mock the parent dispatch to avoid actual view processing
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Test with various languages
            for lang_code in SUPPORTED_LANGUAGE_CODES:
                with self.subTest(language=lang_code):
                    # Create request with X-Language header
                    django_request = self.factory.get('/', HTTP_X_LANGUAGE=lang_code)
                    request = Request(django_request)
                    
                    # Call dispatch
                    self.view.dispatch(request)
                    
                    # Verify language was stored in request
                    assert request._language == lang_code

    def test_dispatch_with_invalid_language_uses_default(self):
        """Test that dispatch uses default language for invalid language headers."""
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Create request with invalid X-Language header
            django_request = self.factory.get('/', HTTP_X_LANGUAGE='invalid')
            request = Request(django_request)
            
            # Call dispatch
            self.view.dispatch(request)
            
            # Verify default language was stored
            assert request._language == DEFAULT_LANGUAGE

    def test_dispatch_with_no_language_header_uses_default(self):
        """Test that dispatch uses default language when no header is provided."""
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Create request without X-Language header
            django_request = self.factory.get('/')
            request = Request(django_request)
            
            # Call dispatch
            self.view.dispatch(request)
            
            # Verify default language was stored
            assert request._language == DEFAULT_LANGUAGE

    def test_get_serializer_context_includes_language(self):
        """Test that get_serializer_context includes language from request."""
        # Create request and set language
        django_request = self.factory.get('/')
        request = Request(django_request)
        request._language = 'en'
        self.view.request = request
        
        # Get serializer context
        context = self.view.get_serializer_context()
        
        # Verify language is in context
        assert 'language' in context
        assert context['language'] == 'en'

    def test_get_serializer_context_without_language_in_request(self):
        """Test get_serializer_context when request has no language attribute."""
        # Create request without language attribute
        django_request = self.factory.get('/')
        request = Request(django_request)
        self.view.request = request
        
        # Get serializer context
        context = self.view.get_serializer_context()
        
        # Language should not be in context
        assert 'language' not in context

    def test_get_serializer_context_calls_super(self):
        """Test that get_serializer_context calls super method if it exists."""
        # Mock parent class method
        with patch.object(MockI18nView.__bases__[1], 'get_serializer_context', 
                         return_value={'existing_key': 'existing_value'}) as mock_super:
            
            # Create request with language
            django_request = self.factory.get('/')
            request = Request(django_request)
            request._language = 'de'
            self.view.request = request
            
            # Get context
            context = self.view.get_serializer_context()
            
            # Verify super was called
            mock_super.assert_called_once()
            
            # Verify both existing and new keys are present
            assert 'existing_key' in context
            assert 'language' in context
            assert context['existing_key'] == 'existing_value'
            assert context['language'] == 'de'

    def test_get_serializer_context_without_super_method(self):
        """Test get_serializer_context when parent class doesn't have the method."""
        # Create a view class without the method in parent
        class TestViewWithoutSuper(I18nViewMixin):
            pass
        
        view = TestViewWithoutSuper()
        
        # Create request with language
        django_request = self.factory.get('/')
        request = Request(django_request)
        request._language = 'uk'
        view.request = request
        
        # Get context
        context = view.get_serializer_context()
        
        # Should only have language key
        assert context == {'language': 'uk'}

    @patch('api.i18n.translation.activate')
    def test_dispatch_integration_with_real_request(self, mock_activate):
        """Test dispatch method with a real request flow."""
        # Mock parent dispatch to return a simple response
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_response = Mock()
            mock_super_dispatch.return_value = mock_response
            
            # Create request
            django_request = self.factory.get('/', HTTP_X_LANGUAGE='de')
            request = Request(django_request)
            
            # Call dispatch
            result = self.view.dispatch(request, arg1='test', kwarg1='test')
            
            # Verify language activation was called
            mock_activate.assert_called_once_with('de')
            
            # Verify super dispatch was called with correct arguments
            mock_super_dispatch.assert_called_once_with(request, arg1='test', kwarg1='test')
            
            # Verify request has language attribute
            assert request._language == 'de'
            
            # Verify return value
            assert result == mock_response

    def test_dispatch_preserves_args_and_kwargs(self):
        """Test that dispatch preserves args and kwargs when calling super."""
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Create request
            django_request = self.factory.get('/')
            request = Request(django_request)
            
            # Call dispatch with args and kwargs
            args = ('arg1', 'arg2')
            kwargs = {'pk': 123, 'format': 'json'}
            
            self.view.dispatch(request, *args, **kwargs)
            
            # Verify super was called with correct arguments
            mock_super_dispatch.assert_called_once_with(request, *args, **kwargs)


class I18nViewMixinIntegrationTests(APITestCase):
    """Integration tests for I18nViewMixin with Django test client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.view = MockI18nView.as_view({'get': 'test_action'})

    def test_full_request_cycle_with_language_header(self):
        """Test full request cycle with X-Language header."""
        # This test would require proper URL setup, so we'll simulate it
        factory = RequestFactory()
        
        for lang_code in SUPPORTED_LANGUAGE_CODES:
            with self.subTest(language=lang_code):
                # Create request with language header
                django_request = factory.get('/', HTTP_X_LANGUAGE=lang_code)
                request = Request(django_request)
                
                # Create view instance and process request
                view_instance = MockI18nView()
                view_instance.setup(request)
                
                # Manually call dispatch (simulating URL routing)
                with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super:
                    mock_super.side_effect = lambda req, *args, **kwargs: view_instance.test_action(req)
                    response = view_instance.dispatch(request)
                
                # Verify response contains correct language
                assert response.status_code == status.HTTP_200_OK
                assert response.data['language'] == lang_code

    def test_full_request_cycle_without_language_header(self):
        """Test full request cycle without X-Language header."""
        factory = RequestFactory()
        
        # Create request without language header
        django_request = factory.get('/')
        request = Request(django_request)
        
        # Create view instance and process request
        view_instance = MockI18nView()
        view_instance.setup(request)
        
        # Manually call dispatch
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super:
            mock_super.side_effect = lambda req, *args, **kwargs: view_instance.test_action(req)
            response = view_instance.dispatch(request)
        
        # Verify response contains default language
        assert response.status_code == status.HTTP_200_OK
        assert response.data['language'] == DEFAULT_LANGUAGE
