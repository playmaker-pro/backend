from rest_framework import serializers
from django.utils.translation import gettext as _
from django.utils import translation

from api.i18n import I18nSerializerMixin
from notifications.models import Notification
from notifications.templates import NotificationTemplate
from utils import GENDER_BASED_ROLES


class NotificationSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for notifications with translation support.
    
    Handles both new template-based notifications (with template_name and parameters)
    and legacy notifications (direct text translation with optional parameter formatting).
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification

        fields = [
            "id",
            "title",
            "description",
            "updated_at",
            "created_at",
            "seen",
            "href",
            "icon",
            "picture",
            "picture_profile_role",
        ]
    
    def get_title(self, obj):
        """Get translated title."""
        return self._translate_field(obj, 'title')
    
    def get_description(self, obj):
        """Get translated description."""
        return self._translate_field(obj, 'description')
    
    def _translate_field(self, obj, field_name):
        """Translate notification field (title or description)."""
        
        # Template-based notifications (preferred)
        if obj.template_name and hasattr(obj, 'template_params') and obj.template_params:
            try:
                template = NotificationTemplate[obj.template_name.upper()]
                template_text = template.value[field_name]
                display_params = self._translate_template_params(obj.template_params)
                return _(template_text).format(**display_params)
            except (KeyError, AttributeError, ValueError):
                # Template approach failed, try fallback with stored text
                pass
        
        # Fallback: translate stored text and try to format with parameters if available
        field_value = getattr(obj, field_name)
        translated_text = _(field_value)
        
        # If we have template parameters, try to format the translated text
        if hasattr(obj, 'template_params') and obj.template_params:
            try:
                display_params = self._translate_template_params(obj.template_params)
                return translated_text.format(**display_params)
            except (KeyError, ValueError):
                # Formatting failed, return just the translated text
                pass
        
        return translated_text
    
    def _translate_template_params(self, template_params):
        """Translate parameters (like roles) within template parameters."""
        display_params = template_params.copy()
        
        # Translate profile roles in the 'profile' parameter
        if 'profile' in display_params:
            display_params['profile'] = self._translate_profile_role(display_params['profile'])
            
        return display_params
    
    def _translate_profile_role(self, profile_text):
        """Translate Polish role in profile text to current language."""
        for role_info in GENDER_BASED_ROLES.values():
            for role in role_info:
                # Get the Polish version of the role for matching
                with translation.override('pl'):
                    polish_role = str(role)
                
                # Check if profile text starts with this Polish role
                if profile_text.startswith(polish_role + ' '):
                    # Translate the role to current language
                    translated_role = _(role)
                    return profile_text.replace(polish_role, str(translated_role), 1)
        
        return profile_text

    def mark_as_read(self) -> None:
        """
        Mark the notification as read
        """
        self.instance.mark_as_read()
        self.instance.save()
        self.instance.refresh_from_db()
