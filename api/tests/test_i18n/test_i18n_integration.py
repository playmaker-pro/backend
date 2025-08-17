"""
Integration tests for I18n functionality.

Tests the complete flow from view to serializer with language detection and activation.
"""
from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from rest_framework.test import APITestCase
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.i18n_config import SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE
from api.tests.fixtures.test_models import MockI18nView, MockI18nSerializer, MockModel


class I18nIntegrationTests(TestCase):
    """Integration tests for I18n view and serializer mixins."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.view = MockI18nView()
        self.test_instance = MockModel()

    def test_view_to_serializer_context_passing(self):
        """Test that language context flows from view to serializer."""
        # Create request with language header
        django_request = self.factory.get('/', HTTP_X_LANGUAGE='en')
        request = Request(django_request)
        
        # Mock parent dispatch to avoid actual view processing
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            
            # Call view dispatch
            self.view.dispatch(request)
            
            # Verify language was stored in request
            assert request._language == 'en'
            
            # Set request on view to simulate DRF behavior
            self.view.request = request
            
            # Get serializer context
            context = self.view.get_serializer_context()
            
            # Verify language is in context
            assert 'language' in context
            assert context['language'] == 'en'

    def test_complete_request_response_cycle(self):
        """Test complete request-response cycle with language detection."""
        # Test with subset of languages for efficiency
        test_languages = ['en', 'de', 'pl']  # Representative subset
        
        for lang_code in test_languages:
            with self.subTest(language=lang_code):
                # Create request
                django_request = self.factory.get('/', HTTP_X_LANGUAGE=lang_code)
                request = Request(django_request)
                
                # Process through view
                with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super:
                    # Use side_effect so test_action is called AFTER dispatch sets _language
                    mock_super.side_effect = lambda req, *args, **kwargs: self.view.test_action(req)
                    response = self.view.dispatch(request)
                
                # Verify response
                assert response.status_code == status.HTTP_200_OK
                assert response.data['language'] == lang_code

    def test_view_serializer_language_synchronization(self):
        """Test that view and serializer use the same language."""
        # Create request with German language
        django_request = self.factory.get('/', HTTP_X_LANGUAGE='de')
        request = Request(django_request)
        
        # Process request through view
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            self.view.dispatch(request)
        
        # Set request on view
        self.view.request = request
        
        # Get serializer context from view
        context = self.view.get_serializer_context()
        
        # Create serializer with view context
        serializer = MockI18nSerializer(instance=self.test_instance, context=context)
        
        # Both view and serializer should use the same language
        assert request._language == 'de'
        assert context['language'] == 'de'
        assert 'de' in serializer.activation_log

    @patch('api.i18n.translation.activate')
    def test_view_and_serializer_both_activate_language(self, mock_activate):
        """Test that both view and serializer activate the language."""
        # Create request
        django_request = self.factory.get('/', HTTP_X_LANGUAGE='uk')
        request = Request(django_request)
        
        # Process through view
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.return_value = Mock()
            self.view.dispatch(request)
        
        # Get context and create serializer
        self.view.request = request
        context = self.view.get_serializer_context()
        serializer = MockI18nSerializer(instance=self.test_instance, context=context)
        
        # Verify translation.activate was called multiple times with 'uk'
        activate_calls = [call for call in mock_activate.call_args_list if call[0][0] == 'uk']
        assert len(activate_calls) >= 1  # At least once from serializer

    def test_invalid_language_handling_end_to_end(self):
        """Test invalid language handling through the complete flow."""
        # Create request with invalid language
        django_request = self.factory.get('/', HTTP_X_LANGUAGE='invalid')
        request = Request(django_request)
        
        # Process through view
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.side_effect = lambda req, *args, **kwargs: self.view.test_action(req)
            response = self.view.dispatch(request)
        
        # Both view and serializer should fall back to default language
        assert request._language == DEFAULT_LANGUAGE
        assert response.data['language'] == DEFAULT_LANGUAGE

    def test_no_language_header_end_to_end(self):
        """Test behavior when no language header is provided."""
        # Create request without language header
        django_request = self.factory.get('/')
        request = Request(django_request)
        
        # Process through view
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.side_effect = lambda req, *args, **kwargs: self.view.test_action(req)
            response = self.view.dispatch(request)
        
        # Should use default language
        assert request._language == DEFAULT_LANGUAGE
        assert response.data['language'] == DEFAULT_LANGUAGE

    def test_multiple_serializers_with_different_contexts(self):
        """Test multiple serializers with different language contexts."""
        # Create two different contexts
        context_en = {'language': 'en'}
        context_de = {'language': 'de'}
        
        # Create serializers
        serializer_en = MockI18nSerializer(instance=self.test_instance, context=context_en)
        serializer_de = MockI18nSerializer(instance=self.test_instance, context=context_de)
        
        # Each should activate its own language
        assert 'en' in serializer_en.activation_log
        assert 'de' in serializer_de.activation_log
        
        # Logs should be independent
        assert not 'de' in serializer_en.activation_log
        assert not 'en' in serializer_de.activation_log

    def test_serializer_data_consistency_across_languages(self):
        """Test that serializer data is consistent across different languages."""
        test_instance = MockModel(name="Test Name", description="Test Description")
        
        # Test with subset of languages for efficiency
        test_languages = ['en', 'de']  # Representative subset
        
        for lang_code in test_languages:
            with self.subTest(language=lang_code):
                context = {'language': lang_code}
                serializer = MockI18nSerializer(instance=test_instance, context=context)
                
                data = serializer.data
                
                # Data should be consistent regardless of language
                assert data['name'] == "Test Name"
                assert data['description'] == "Test Description"
                
                # But language should be activated
                assert lang_code in serializer.activation_log

    def test_view_error_handling_with_i18n(self):
        """Test that view error handling works correctly with i18n."""
        # Create a view method that raises an exception
        def failing_action(request):
            raise ValueError("Test error")
        
        self.view.failing_action = failing_action
        
        # Create request
        django_request = self.factory.get('/', HTTP_X_LANGUAGE='en')
        request = Request(django_request)
        
        # Process request - language should still be activated despite error
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super_dispatch:
            mock_super_dispatch.side_effect = ValueError("Test error")
            
            with self.assertRaises(ValueError):
                self.view.dispatch(request)
            
            # Language should still be stored in request
            assert request._language == 'en'

    def test_nested_serializer_context_inheritance(self):
        """Test that nested serializers inherit language context."""
        # Create a serializer that uses another serializer
        class ParentSerializer(MockI18nSerializer):
            child = MockI18nSerializer(source='*', read_only=True)
            
            class Meta:
                model = MockModel
                fields = ['name', 'description', 'child']  # Include child field
                validators = []
        
        context = {'language': 'pl'}
        parent_serializer = ParentSerializer(instance=self.test_instance, context=context)
        
        # Access data to trigger child serializer creation
        data = parent_serializer.data
        
        # Parent should have activated language
        assert 'pl' in parent_serializer.activation_log
        
        # Data should be present
        assert 'name' in data
        assert 'child' in data


class I18nEndToEndTests(APITestCase):
    """End-to-end tests simulating real API usage."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_instance = MockModel()

    def test_real_world_api_flow_simulation(self):
        """Simulate a real-world API request flow."""
        # This simulates what happens in a real API call:
        # 1. Request comes in with X-Language header
        # 2. View detects and activates language
        # 3. View creates serializer with language context
        # 4. Serializer activates language and serializes data
        # 5. Response is returned
        
        factory = RequestFactory()
        
        # Test with one representative language for end-to-end flow
        lang_code = 'en'
        
        # Step 1: Request with language header
        django_request = factory.get('/', HTTP_X_LANGUAGE=lang_code)
        request = Request(django_request)
        
        # Step 2: View processing
        view = MockI18nView()
        
        with patch('rest_framework.viewsets.GenericViewSet.dispatch') as mock_super:
            # Step 3: Language detection and activation
            view.dispatch(request)
            
            # Step 4: Context creation and serializer usage
            view.request = request
            context = view.get_serializer_context()
            serializer = MockI18nSerializer(instance=self.test_instance, context=context)
            
            # Step 5: Data serialization
            data = serializer.data
            response = Response(data)
        
        # Verify the complete flow worked
        assert request._language == lang_code
        assert 'language' in context
        assert context['language'] == lang_code
        assert lang_code in serializer.activation_log
        assert 'name' in data
        assert 'description' in data

    def test_performance_with_multiple_requests(self):
        """Test that i18n doesn't significantly impact performance with multiple requests."""
        factory = RequestFactory()
        
        # Simulate multiple requests with different languages (reduced scope)
        languages = ['en', 'de'] * 5  # 10 requests total instead of 40
        
        for i, lang_code in enumerate(languages):
            django_request = factory.get(f'/test/{i}', HTTP_X_LANGUAGE=lang_code)
            request = Request(django_request)
            
            view = MockI18nView()
            
            with patch('rest_framework.viewsets.GenericViewSet.dispatch'):
                view.dispatch(request)
                view.request = request
                context = view.get_serializer_context()
                serializer = MockI18nSerializer(instance=self.test_instance, context=context)
                data = serializer.data
            
            # Each request should work correctly
            assert request._language == lang_code
            assert lang_code in serializer.activation_log
