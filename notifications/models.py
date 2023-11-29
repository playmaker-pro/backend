import typing

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import JSONField


class NotificationSetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    weekly_report = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} notification settings"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("BI", "built-in"),
        ("CO", "contacts"),
        ("MA", "marketing"),
        ("FO", "follow"),
        ("SE", "seasonal"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=2, choices=NOTIFICATION_TYPES)
    event_type = models.CharField(max_length=100)
    details = JSONField(null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")


class NotificationTemplate(models.Model):
    event_type = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=50)
    content_template = models.TextField(
        help_text="Use placeholders for dynamic content"
    )

    def __str__(self):
        return f"{self.event_type} - {self.notification_type}"

    def render_content(
        self, user: settings.AUTH_USER_MODEL, context: typing.Dict[str, typing.Any]
    ) -> str:
        """
        Replace placeholders in the content_template with actual values from the context.
        """
        from notifications.utils import NotificationContentParser

        parser = NotificationContentParser(user, **context)
        return parser.parse(self.content_template)
