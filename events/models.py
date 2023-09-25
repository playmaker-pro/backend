from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


class NotificationEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    callback = models.URLField(null=True, blank=True)
    seen = models.BooleanField(default=False)
    seen_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.message}"

    class Meta:
        unique_together = ("user", "created_at", "message")
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "seen",
                ]
            ),
        ]
