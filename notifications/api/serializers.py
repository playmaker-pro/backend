from rest_framework import serializers
from django.utils.translation import gettext as _

from api.i18n import I18nSerializerMixin
from notifications.models import Notification
from notifications.templates import NotificationTemplate


class NotificationSerializer(I18nSerializerMixin, serializers.ModelSerializer):
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
        # New way: use template_name + template_params for proper translation
        if obj.template_name and hasattr(obj, 'template_params') and obj.template_params:
            try:
                template = NotificationTemplate[obj.template_name.upper()]
                title_template = template.value['title']
                return _(title_template).format(**obj.template_params)
            except (KeyError, AttributeError, ValueError):
                pass
        
        # Fallback: try basic translation of stored title
        return _(obj.title)
    
    def get_description(self, obj):
        """Get translated description."""
        # New way: use template_name + template_params for proper translation
        if obj.template_name and hasattr(obj, 'template_params') and obj.template_params:
            try:
                template = NotificationTemplate[obj.template_name.upper()]
                desc_template = template.value['description']
                return _(desc_template).format(**obj.template_params)
            except (KeyError, AttributeError, ValueError):
                pass
        
        # Fallback: try basic translation of stored description
        return _(obj.description)

    def mark_as_read(self) -> None:
        """
        Mark the notification as read
        """
        self.instance.mark_as_read()
        self.instance.save()
        self.instance.refresh_from_db()
