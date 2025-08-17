"""
Internationalization utilities and mixins for API views and serializers.

This module provides flexible language handling for Django REST API endpoints,
supporting multiple language detection methods and translation activation.
"""

import logging
from typing import Optional

from django.utils import translation
from rest_framework.request import Request
from rest_framework.response import Response

from .i18n_config import SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE


logger = logging.getLogger(__name__)


class LanguageDetectionMixin:
    """
    Mixin for detecting and activating language from X-Language header.

    Language detection:
    1. X-Language HTTP header
    2. Default language from settings
    """

    def get_request_language(self, request: Optional[Request] = None) -> str:
        """
        Determine the language for the current request.
        """
        if not request:
            return DEFAULT_LANGUAGE
            
        # X-Language header
        try:
            x_language = request.headers.get('X-Language')
            if x_language and x_language.lower() in SUPPORTED_LANGUAGE_CODES:
                return x_language.lower()
        except AttributeError:
            # Request doesn't have headers attribute
            logger.debug("Request has no headers attribute")

        # Default language
        return DEFAULT_LANGUAGE

    def activate_language(self, language: str) -> str:
        """
        Activate the specified language for Django's translation system.
        """
        if language in SUPPORTED_LANGUAGE_CODES:
            translation.activate(language)
            return language
        else:
            logger.warning(f"Unsupported language '{language}', using default '{DEFAULT_LANGUAGE}'")
            translation.activate(DEFAULT_LANGUAGE)
            return DEFAULT_LANGUAGE


class I18nViewMixin(LanguageDetectionMixin):
    """
    Mixin for API views that need internationalization support.

    Usage:
        class MyAPIView(I18nViewMixin, APIView):
            def get(self, request):
                # Language is automatically detected and activated
                return Response(self.get_localized_data())
    """

    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        """
        Override dispatch to activate language before processing request.
        """
        language = self.get_request_language(request)
        self.activate_language(language)

        # Store language in request for serializers
        request._language = language

        return super().dispatch(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Add language to serializer context.
        """
        context = super().get_serializer_context() if hasattr(super(), 'get_serializer_context') else {}
        if hasattr(self.request, '_language'):
            context['language'] = self.request._language
        return context


class I18nSerializerMixin(LanguageDetectionMixin):
    """
    Mixin for serializers that need internationalization support.

    Usage:
        class MySerializer(I18nSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = '__all__'

            def to_representation(self, instance):
                # Translations are automatically activated
                return super().to_representation(instance)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._activate_context_language()

    def _activate_context_language(self) -> None:
        """
        Activate language from context if available.
        """
        if hasattr(self, 'context') and self.context:
            language = self.context.get('language')
            if language:
                self.activate_language(language)
                return

        # Fallback to current language
        current_language = translation.get_language()
        if current_language:
            self.activate_language(current_language)
