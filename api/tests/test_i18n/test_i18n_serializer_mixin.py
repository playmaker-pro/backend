"""
Tests for I18nSerializerMixin functionality.
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import translation

from api.i18n import I18nSerializerMixin
from api.i18n_config import SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE
from api.tests.fixtures.test_models import MockI18nSerializer, MockModel, create_mock_context
from rest_framework.serializers import ModelSerializer


class I18nSerializerMixinTests(TestCase):
    """Test cases for I18nSerializerMixin."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_instance = MockModel()

    def test_init_calls_activate_context_language(self):
        """Test that __init__ calls _activate_context_language."""
        with patch.object(MockI18nSerializer, '_activate_context_language') as mock_activate:
            serializer = MockI18nSerializer(instance=self.test_instance)
            mock_activate.assert_called_once()

    def test_activate_context_language_with_valid_context_language(self):
        """Test language activation with valid language in context."""
        for lang_code in SUPPORTED_LANGUAGE_CODES:
            with self.subTest(language=lang_code):
                context = create_mock_context(language=lang_code)
                serializer = MockI18nSerializer(instance=self.test_instance, context=context)
                
                # Check that language was activated
                assert lang_code in serializer.activation_log

    def test_activate_context_language_with_invalid_context_language(self):
        """Test language activation with invalid language in context."""
        invalid_languages = ['fr', 'es', 'invalid', '123']
        
        for invalid_lang in invalid_languages:
            with self.subTest(language=invalid_lang):
                context = create_mock_context(language=invalid_lang)
                serializer = MockI18nSerializer(instance=self.test_instance, context=context)
                
                # Should activate default language for invalid language
                assert DEFAULT_LANGUAGE in serializer.activation_log

    def test_context_fallback_scenarios(self):
        """Test various context fallback scenarios in a parameterized way."""
        fallback_scenarios = [
            ({'other_key': 'other_value'}, 'en', 'no language key'),
            ({}, 'pl', 'empty context'),
            (None, 'de', 'None context'),
            ({'language': None}, 'uk', 'None language value'),
            ({'language': ''}, 'pl', 'empty language value'),  # Empty string should fall back to current, then validated
        ]
        
        for context, expected_lang, scenario in fallback_scenarios:
            with self.subTest(scenario=scenario):
                with patch('api.i18n.translation.get_language', return_value=expected_lang) as mock_get_lang:
                    serializer = MockI18nSerializer(instance=self.test_instance, context=context)
                    
                    # Should fall back to current language
                    mock_get_lang.assert_called_once()
                    assert expected_lang in serializer.activation_log

    def test_activation_priority_context_over_current(self):
        """Test that context language takes priority over current language."""
        context = create_mock_context(language='en')
        
        with patch('api.i18n.translation.get_language', return_value='pl') as mock_get_lang:
            serializer = MockI18nSerializer(instance=self.test_instance, context=context)
            
            # Should activate context language, not current language
            assert 'en' in serializer.activation_log
            # get_language should not be called when context language is available
            mock_get_lang.assert_not_called()

    def test_multiple_serializer_instances_independent_activation(self):
        """Test that multiple serializer instances have independent language activation."""
        context_en = create_mock_context(language='en')
        context_de = create_mock_context(language='de')
        
        serializer_en = MockI18nSerializer(instance=self.test_instance, context=context_en)
        serializer_de = MockI18nSerializer(instance=self.test_instance, context=context_de)
        
        # Each serializer should have activated its own language
        assert 'en' in serializer_en.activation_log
        assert 'de' in serializer_de.activation_log
        
        # Each serializer should only have its own language in log
        assert len(serializer_en.activation_log) == 1
        assert len(serializer_de.activation_log) == 1

    def test_serialization_with_language_activation(self):
        """Test that serialization works correctly after language activation."""
        context = create_mock_context(language='en')
        serializer = MockI18nSerializer(instance=self.test_instance, context=context)
        
        # Serialize the data
        data = serializer.data
        
        # Verify serialization worked
        assert 'name' in data
        assert 'description' in data
        assert data['name'] == 'Test Name'
        assert data['description'] == 'Test Description'
        
        # Verify language was activated
        assert 'en' in serializer.activation_log

    @patch.object(I18nSerializerMixin, 'activate_language')
    def test_activate_context_language_calls_activate_language(self, mock_activate):
        """Test that _activate_context_language calls activate_language method."""
        mock_activate.return_value = 'en'
        
        context = create_mock_context(language='en')
        serializer = MockI18nSerializer(instance=self.test_instance, context=context)
        
        # Verify activate_language was called with correct language
        mock_activate.assert_called_with('en')


    def test_serializer_inheritance_chain(self):
        """Test that the mixin works correctly in inheritance chain."""
        # Create a more complex inheritance chain
        class CustomTestSerializer(MockI18nSerializer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.custom_init_called = True
        
        context = create_mock_context(language='uk')
        serializer = CustomTestSerializer(instance=self.test_instance, context=context)
        
        # Verify both parent and child init were called
        assert hasattr(serializer, 'custom_init_called')
        assert serializer.custom_init_called
        
        # Verify language activation still works
        assert 'uk' in serializer.activation_log


class I18nSerializerMixinIntegrationTests(TestCase):
    """Integration tests for I18nSerializerMixin."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_instance = MockModel()

    @patch('api.i18n.translation.activate')
    def test_integration_with_django_translation_system(self, mock_activate):
        """Test integration with Django's translation system."""
        context = create_mock_context(language='en')
        serializer = MockI18nSerializer(instance=self.test_instance, context=context)
        
        # Verify Django's translation.activate was called
        mock_activate.assert_called_with('en')
        
        # Verify serialization still works
        data = serializer.data
        assert'name' in data

    def test_without_mixin_for_comparison(self):
        """Test serializer behavior without mixin for comparison."""
        from rest_framework.serializers import ModelSerializer
        
        class PlainSerializer(ModelSerializer):
            class Meta:
                model = MockModel
                fields = ['name', 'description']
        
        # Plain serializer should work without language activation
        plain_serializer = PlainSerializer(instance=self.test_instance)
        data = plain_serializer.data
        
        assert 'name' in data
        assert 'description' in data
        
        # But it shouldn't have activation tracking
        assert not hasattr(plain_serializer, 'activation_log')

    def test_multiple_field_serialization_with_translation(self):
        """Test serialization of multiple fields with translation active."""
        test_instance = MockModel(name="Custom Name", description="Custom Description")
        context = create_mock_context(language='de')
        
        serializer = MockI18nSerializer(instance=test_instance, context=context)
        data = serializer.data
        
        # Verify all fields are serialized correctly
        assert data['name'] == "Custom Name"
        assert data['description'] == "Custom Description"
        
        # Verify language was activated
        assert 'de' in serializer.activation_log
