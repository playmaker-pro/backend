
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class NotificationSetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    weekly_report = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user} notification settings'
