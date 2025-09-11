"""
End-to-end tests for the I18n functionality.

These tests validate the complete flow from an incoming request with a language header
to the final response, ensuring that the view and serializer mixins work together correctly.
"""
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from api.i18n_config import DEFAULT_LANGUAGE
from api.tests.fixtures.test_models import TestI18nView, TestI18nSerializer


class I18nEndToEndTests(TestCase):
    """End-to-end tests for the I18n request-response cycle."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.view = TestI18nView()

    def _simulate_request_cycle(self, language: str):
        """Simulate a full request-response cycle for a given language."""
        # Create a Django request with the specified language header
        headers = {'HTTP_X_LANGUAGE': language} if language else {}
        django_request = self.factory.get('/', **headers)
        
        # 1. Simulate the view dispatch process (without actual DRF dispatch)
        # This mimics what happens in I18nViewMixin.dispatch()
        from api.i18n import I18nViewMixin
        from rest_framework.request import Request
        
        # Create DRF request
        request = Request(django_request)
        
        # Manually call the language detection and activation logic
        detected_language = self.view.get_request_language(request)
        self.view.activate_language(detected_language)
        request._language = detected_language
        
        # Set request on view
        self.view.request = request

        # 2. View creates the serializer context
        context = self.view.get_serializer_context()

        # 3. Serializer is initialized with the context
        serializer = TestI18nSerializer(context=context)

        return request, context, serializer

    def test_end_to_end_flow_with_valid_language(self):
        """Test the complete flow with a valid language header."""
        lang_code = 'de'
        request, context, serializer = self._simulate_request_cycle(lang_code)

        # Verify that the language is correctly handled at each stage
        assert request._language == lang_code
        assert context.get('language') == lang_code
        assert lang_code in serializer.activation_log

    def test_end_to_end_flow_with_invalid_language(self):
        """Test the complete flow with an invalid language header."""
        request, context, serializer = self._simulate_request_cycle('invalid-lang')

        # Verify that the system falls back to the default language
        assert request._language == DEFAULT_LANGUAGE
        assert context.get('language') == DEFAULT_LANGUAGE
        assert DEFAULT_LANGUAGE in serializer.activation_log

    def test_end_to_end_flow_without_language_header(self):
        """Test the complete flow when no language header is provided."""
        request, context, serializer = self._simulate_request_cycle(None)

        # Verify that the system uses the default language
        assert request._language == DEFAULT_LANGUAGE
        assert context.get('language') == DEFAULT_LANGUAGE
        assert DEFAULT_LANGUAGE in serializer.activation_log
