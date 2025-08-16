"""
Tests for LanguageDetectionMixin functionality.
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import translation

from api.i18n import LanguageDetectionMixin
from api.i18n_config import SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE
from ..fixtures.test_models import create_mock_request


class LanguageDetectionMixinTests(TestCase):
    """Test cases for LanguageDetectionMixin."""

    def setUp(self):
        """Set up test fixtures."""
        self.mixin = LanguageDetectionMixin()
    
    def test_get_request_language_with_valid_x_language_header(self):
        """Test language detection from valid X-Language header."""
        for lang_code in SUPPORTED_LANGUAGE_CODES:
            with self.subTest(language=lang_code):
                request = create_mock_request(headers={'X-Language': lang_code})
                result = self.mixin.get_request_language(request)
                assert result == lang_code
    
    def test_get_request_language_with_valid_x_language_header_mixed_case(self):
        """Test language detection with mixed case X-Language header."""
        test_cases = [
            ('EN', 'en'),
            ('De', 'de'),
            ('PL', 'pl'),
            ('uK', 'uk')
        ]
        
        for input_lang, expected_lang in test_cases:
            with self.subTest(input=input_lang, expected=expected_lang):
                request = create_mock_request(headers={'X-Language': input_lang})
                result = self.mixin.get_request_language(request)
                assert result == expected_lang
    
    def test_get_request_language_with_invalid_x_language_header(self):
        """Test language detection with invalid X-Language header."""
        invalid_languages = ['fr', 'es', 'invalid', '123', '']
        
        for invalid_lang in invalid_languages:
            with self.subTest(language=invalid_lang):
                request = create_mock_request(headers={'X-Language': invalid_lang})
                result = self.mixin.get_request_language(request)
                assert result == DEFAULT_LANGUAGE
    
    def test_get_request_language_with_no_x_language_header(self):
        """Test language detection without X-Language header."""
        request = create_mock_request(headers={})
        result = self.mixin.get_request_language(request)
        assert result == DEFAULT_LANGUAGE
    
    def test_get_request_language_with_none_request(self):
        """Test language detection with None request."""
        result = self.mixin.get_request_language(None)
        assert result == DEFAULT_LANGUAGE
    
    def test_get_request_language_with_missing_headers_attribute(self):
        """Test language detection when request has no headers attribute."""
        request = Mock(spec=[])  # Create mock without headers attribute
        result = self.mixin.get_request_language(request)
        assert result == DEFAULT_LANGUAGE
    
    @patch('api.i18n.translation.activate')
    @patch('api.i18n.logger')
    def test_activate_language_with_valid_language(self, mock_logger, mock_activate):
        """Test language activation with valid language."""
        for lang_code in SUPPORTED_LANGUAGE_CODES:
            with self.subTest(language=lang_code):
                result = self.mixin.activate_language(lang_code)
                
                # Verify translation.activate was called
                mock_activate.assert_called_with(lang_code)
                
                # Verify logging
                mock_logger.debug.assert_called_with(f"Activated language: {lang_code}")
                
                # Verify return value
                assert result == lang_code
                
                # Reset mocks
                mock_activate.reset_mock()
                mock_logger.reset_mock()
    
    @patch('api.i18n.translation.activate')
    @patch('api.i18n.logger')
    def test_activate_language_with_invalid_language(self, mock_logger, mock_activate):
        """Test language activation with invalid language."""
        invalid_languages = ['fr', 'es', 'invalid', '123']
        
        for invalid_lang in invalid_languages:
            with self.subTest(language=invalid_lang):
                result = self.mixin.activate_language(invalid_lang)
                
                # Verify translation.activate was called with default language
                mock_activate.assert_called_with(DEFAULT_LANGUAGE)
                
                # Verify warning was logged
                mock_logger.warning.assert_called_with(
                    f"Unsupported language '{invalid_lang}', using default '{DEFAULT_LANGUAGE}'"
                )
                
                # Verify return value
                assert result == DEFAULT_LANGUAGE
                
                # Reset mocks
                mock_activate.reset_mock()
                mock_logger.reset_mock()
    
    @patch('api.i18n.translation.activate')
    def test_activate_language_with_empty_string(self, mock_activate):
        """Test language activation with empty string."""
        result = self.mixin.activate_language('')
        
        # Should activate default language
        mock_activate.assert_called_with(DEFAULT_LANGUAGE)
        assert result == DEFAULT_LANGUAGE
    
    @patch('api.i18n.translation.activate')
    def test_activate_language_with_none(self, mock_activate):
        """Test language activation with None."""
        result = self.mixin.activate_language(None)
        
        # Should activate default language
        mock_activate.assert_called_with(DEFAULT_LANGUAGE)
        assert result == DEFAULT_LANGUAGE
    
    @patch('api.i18n.logger')
    def test_get_request_language_logging(self, mock_logger):
        """Test that appropriate debug messages are logged."""
        # Test X-Language header detection logging
        request = create_mock_request(headers={'X-Language': 'en'})
        self.mixin.get_request_language(request)
        mock_logger.debug.assert_called_with("Language detected from X-Language header: en")
        
        # Test default language logging
        mock_logger.reset_mock()
        request = create_mock_request(headers={})
        self.mixin.get_request_language(request)
        mock_logger.debug.assert_called_with(f"Using default language: {DEFAULT_LANGUAGE}")
    
    def test_supported_language_codes_configuration(self):
        """Test that supported language codes are properly configured."""
        # Verify SUPPORTED_LANGUAGE_CODES is not empty
        assert len(SUPPORTED_LANGUAGE_CODES) > 0
        
        # Verify DEFAULT_LANGUAGE is in supported languages
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGE_CODES
        
        # Verify all languages are lowercase strings
        for lang in SUPPORTED_LANGUAGE_CODES:
            assert isinstance(lang, str)
            assert lang == lang.lower()
            assert len(lang) >= 2  # ISO language codes are at least 2 characters
