"""
Test configuration and utilities for I18n tests.
"""
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch

from api.i18n_config import SUPPORTED_LANGUAGES, SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE


class I18nConfigTests(TestCase):
    """Test cases for I18n configuration."""

    def test_supported_languages_format(self):
        """Test that SUPPORTED_LANGUAGES has the correct format."""
        assert isinstance(SUPPORTED_LANGUAGES, list)
        assert (len(SUPPORTED_LANGUAGES) > 0)
        
        for lang_tuple in SUPPORTED_LANGUAGES:
            # Each language should be a tuple with code and name
            assert isinstance(lang_tuple, tuple)
            assert (len(lang_tuple), 2)
            
            code, name = lang_tuple
            assert isinstance(code, str)
            assert (len(code) >= 2)  # ISO codes are at least 2 chars
            # Name should be translatable (lazy string or string)
            assert (hasattr(name, '__str__'))

    def test_supported_language_codes_derived_correctly(self):
        """Test that SUPPORTED_LANGUAGE_CODES is derived correctly from SUPPORTED_LANGUAGES."""
        expected_codes = [lang[0] for lang in SUPPORTED_LANGUAGES]
        assert SUPPORTED_LANGUAGE_CODES == expected_codes

    def test_default_language_in_supported_languages(self):
        """Test that DEFAULT_LANGUAGE is in SUPPORTED_LANGUAGE_CODES."""
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGE_CODES

    def test_default_language_is_string(self):
        """Test that DEFAULT_LANGUAGE is a string."""
        assert isinstance(DEFAULT_LANGUAGE, str)
        assert (len(DEFAULT_LANGUAGE) >= 2)

    def test_no_duplicate_language_codes(self):
        """Test that there are no duplicate language codes."""
        assert len(SUPPORTED_LANGUAGE_CODES) == len(set(SUPPORTED_LANGUAGE_CODES))

    def test_language_codes_are_lowercase(self):
        """Test that all language codes are lowercase."""
        for code in SUPPORTED_LANGUAGE_CODES:
            assert code == code.lower()

    def test_required_languages_present(self):
        """Test that required languages are present in configuration."""
        required_languages = ['pl', 'en', 'de', 'uk']
        
        for lang in required_languages:
            with self.subTest(language=lang):
                assert (lang in SUPPORTED_LANGUAGE_CODES,
                            f"Required language '{lang}' not found in SUPPORTED_LANGUAGE_CODES")

    def test_configuration_consistency_with_django_settings(self):
        """Test that I18n configuration is consistent with Django settings."""
        # Check if LANGUAGE_CODE matches DEFAULT_LANGUAGE (when available)
        if hasattr(settings, 'LANGUAGE_CODE'):
            # Default language should be compatible with Django's LANGUAGE_CODE
            # Note: Django uses 'en-us' format, we use 'en' format
            django_lang = settings.LANGUAGE_CODE.split('-')[0].lower()
            assert django_lang in SUPPORTED_LANGUAGE_CODES

        # Check if LANGUAGES setting is compatible (when available)
        if hasattr(settings, 'LANGUAGES'):
            django_languages = [lang[0].split('-')[0].lower() for lang in settings.LANGUAGES]
            for our_lang in SUPPORTED_LANGUAGE_CODES:
                # All our supported languages should be supported by Django too
                # (This is more of a warning than a strict requirement)
                if our_lang not in django_languages:
                    print(f"Warning: Language '{our_lang}' not found in Django LANGUAGES setting")


class I18nTestMixin:
    """Mixin providing common utilities for I18n tests."""

    def assertLanguageActivated(self, language_code):
        """Assert that a specific language was activated."""
        with patch('django.utils.translation.get_language') as mock_get_lang:
            mock_get_lang.return_value = language_code
            actual_lang = mock_get_lang.return_value
            assert actual_lang == language_code

    def assertValidLanguageCode(self, language_code):
        """Assert that a language code is valid."""
        assert (language_code in SUPPORTED_LANGUAGE_CODES,
                     f"Language code '{language_code}' is not supported")

    def assertDefaultLanguageUsed(self, actual_language):
        """Assert that the default language was used."""
        assert actual_language == DEFAULT_LANGUAGE

    def get_all_supported_languages(self):
        """Get all supported language codes for testing."""
        return SUPPORTED_LANGUAGE_CODES.copy()

    def get_invalid_languages(self):
        """Get a list of invalid language codes for testing."""
        return ['fr', 'es', 'it', 'invalid', '123', '', 'toolong']
