"""
Consolidated tests for I18n core functionality.

Tests language detection, activation, and mixin behavior in a focused manner.
"""

from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from api.i18n import LanguageDetectionMixin
from api.i18n_config import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGE_CODES,
    SUPPORTED_LANGUAGES,
)
from api.tests.fixtures.test_models import (
    TestI18nSerializer,
    TestI18nView,
    create_mock_context,
    create_mock_request,
)


class I18nConfigTests(TestCase):
    """Test I18n configuration validity."""

    def test_config_structure_and_consistency(self):
        """Test that I18n configuration is properly structured and consistent."""
        # Basic structure validation
        assert isinstance(SUPPORTED_LANGUAGES, list)
        assert len(SUPPORTED_LANGUAGES) > 0
        assert isinstance(DEFAULT_LANGUAGE, str)
        assert len(DEFAULT_LANGUAGE) >= 2

        # Consistency validation
        expected_codes = [lang[0] for lang in SUPPORTED_LANGUAGES]
        assert SUPPORTED_LANGUAGE_CODES == expected_codes
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGE_CODES

        # Format validation
        for lang_tuple in SUPPORTED_LANGUAGES:
            code, name = lang_tuple
            assert isinstance(code, str)
            # Allow both lowercase and mixed-case language codes (e.g., 'en', 'uk-UA')
            assert len(code) >= 2
            # Validate format: should be letters and hyphens only
            assert all(c.isalpha() or c == '-' for c in code)

        # No duplicates
        assert len(SUPPORTED_LANGUAGE_CODES) == len(set(SUPPORTED_LANGUAGE_CODES))


class LanguageDetectionMixinTests(TestCase):
    """Test core language detection logic."""

    def setUp(self):
        self.mixin = LanguageDetectionMixin()

    def test_language_detection_flow(self):
        """Test the complete language detection flow."""
        test_cases = [
            # (headers, expected_language, description)
            ({"X-Language": "en"}, "en", "valid header"),
            ({"X-Language": "DE"}, "de", "mixed case header"),
            ({"X-Language": "uk-UA"}, "uk-UA", "Ukrainian mixed case"),
            ({"X-Language": "uk-ua"}, "uk-UA", "Ukrainian lowercase"),
            ({"X-Language": "UK-UA"}, "uk-UA", "Ukrainian uppercase"),
            ({"X-Language": "invalid"}, DEFAULT_LANGUAGE, "invalid language"),
            ({}, DEFAULT_LANGUAGE, "no header"),
            ({"Other-Header": "value"}, DEFAULT_LANGUAGE, "different header"),
        ]

        for headers, expected, description in test_cases:
            with self.subTest(case=description):
                request = create_mock_request(headers=headers)
                result = self.mixin.get_request_language(request)
                assert result == expected

    def test_edge_cases(self):
        """Test edge cases for language detection."""
        # None request
        assert self.mixin.get_request_language(None) == DEFAULT_LANGUAGE

        # Request without headers attribute
        request_no_headers = Mock(spec=[])
        assert self.mixin.get_request_language(request_no_headers) == DEFAULT_LANGUAGE

    @patch("api.i18n.translation.activate")
    @patch("api.i18n.logger")
    def test_language_activation(self, mock_logger, mock_activate):
        """Test language activation with valid and invalid languages."""
        # Valid language
        result = self.mixin.activate_language("en")
        mock_activate.assert_called_with("en")
        assert result == "en"

        # Invalid language
        mock_activate.reset_mock()
        mock_logger.reset_mock()

        result = self.mixin.activate_language("invalid")
        mock_activate.assert_called_with(DEFAULT_LANGUAGE)
        mock_logger.warning.assert_called_once()
        assert result == DEFAULT_LANGUAGE


class I18nViewMixinTests(TestCase):
    """Test view mixin functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestI18nView()

    @patch("api.i18n.translation.activate")
    def test_dispatch_language_handling(self, mock_activate):
        """Test that dispatch detects and activates language correctly."""
        with patch("rest_framework.viewsets.GenericViewSet.dispatch") as mock_super:
            mock_super.return_value = Mock()

            # Test with valid language
            django_request = self.factory.get("/", HTTP_X_LANGUAGE="en")
            request = Request(django_request)

            self.view.dispatch(request)

            # Verify language detection and activation
            assert request._language == "en"
            mock_activate.assert_called_with("en")

    def test_serializer_context_with_language(self):
        """Test that serializer context includes detected language."""
        # Setup request with language
        django_request = self.factory.get("/")
        request = Request(django_request)
        request._language = "de"
        self.view.request = request

        # Mock the parent get_serializer_context to return a basic context
        with patch(
            "rest_framework.viewsets.GenericViewSet.get_serializer_context",
            return_value={"base": "context"},
        ):
            context = self.view.get_serializer_context()

        assert "language" in context
        assert context["language"] == "de"
        assert "base" in context  # Ensure parent context is preserved


class I18nSerializerMixinTests(TestCase):
    """Test serializer mixin functionality."""

    def test_context_language_activation(self):
        """Test that serializer activates language from context."""
        context = create_mock_context(language="en")
        serializer = TestI18nSerializer(context=context)

        # Language should be activated
        assert "en" in serializer.activation_log

    def test_fallback_behavior(self):
        """Test serializer fallback when no context language."""
        with patch("api.i18n.translation.get_language", return_value="de"):
            serializer = TestI18nSerializer(context={})
            assert "de" in serializer.activation_log

    def test_invalid_context_language(self):
        """Test serializer behavior with invalid context language."""
        context = create_mock_context(language="invalid")
        serializer = TestI18nSerializer(context=context)

        # Should fall back to default language
        assert DEFAULT_LANGUAGE in serializer.activation_log


class I18nMixinIntegrationTests(TestCase):
    """Test integration between view and serializer mixins."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = TestI18nView()

    def test_view_to_serializer_language_flow(self):
        """Test that language flows correctly from view to serializer."""
        # Create request with language
        django_request = self.factory.get("/", HTTP_X_LANGUAGE="en")
        request = Request(django_request)

        # Process through view
        with patch("rest_framework.viewsets.GenericViewSet.dispatch"):
            self.view.dispatch(request)
            self.view.request = request

            # Get context and create serializer with mocked parent context
            with patch(
                "rest_framework.viewsets.GenericViewSet.get_serializer_context",
                return_value={},
            ):
                context = self.view.get_serializer_context()
            serializer = TestI18nSerializer(context=context)

        # Verify language flows through the chain
        assert request._language == "en"
        assert context["language"] == "en"
        assert "en" in serializer.activation_log

    def test_multiple_languages_handling(self):
        """Test handling of different languages in the same application."""
        test_languages = ["en", "de", "pl", "uk-UA"]

        for lang_code in test_languages:
            with self.subTest(language=lang_code):
                # Create request
                django_request = self.factory.get("/", HTTP_X_LANGUAGE=lang_code)
                request = Request(django_request)

                # Process through view
                with patch("rest_framework.viewsets.GenericViewSet.dispatch"):
                    self.view.dispatch(request)
                    self.view.request = request

                    # Create serializer with mocked parent context
                    with patch(
                        "rest_framework.viewsets.GenericViewSet.get_serializer_context",
                        return_value={},
                    ):
                        context = self.view.get_serializer_context()
                    serializer = TestI18nSerializer(context=context)

                # Each language should be handled correctly
                assert request._language == lang_code
                assert lang_code in serializer.activation_log

    def test_invalid_language_end_to_end(self):
        """Test invalid language handling through complete flow."""
        django_request = self.factory.get("/", HTTP_X_LANGUAGE="invalid")
        request = Request(django_request)

        with patch("rest_framework.viewsets.GenericViewSet.dispatch"):
            self.view.dispatch(request)
            self.view.request = request

            # Get context with mocked parent context
            with patch(
                "rest_framework.viewsets.GenericViewSet.get_serializer_context",
                return_value={},
            ):
                context = self.view.get_serializer_context()
            serializer = TestI18nSerializer(context=context)

        # Should fall back to default language throughout
        assert request._language == DEFAULT_LANGUAGE
        assert context["language"] == DEFAULT_LANGUAGE
        assert DEFAULT_LANGUAGE in serializer.activation_log
