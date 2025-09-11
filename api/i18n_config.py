"""
Centralized configuration for internationalization (i18n).

This module consolidates all i18n-related settings, making it easier to manage
supported languages, default language, and other related configurations.
"""

from django.utils.translation import gettext_lazy as _

# Supported languages for the application
SUPPORTED_LANGUAGES = [
    ('pl', _('Polski')),
    ('en', _('English')),
    ('de', _('Deutsch')),
    ('uk', _('Українська')),
]

# List of language codes
SUPPORTED_LANGUAGE_CODES = [lang[0] for lang in SUPPORTED_LANGUAGES]

# Default language code
DEFAULT_LANGUAGE = 'pl'

