from urllib.parse import urljoin

from django.conf import settings
from django.db import models


class Notification(models.Model):
    target = models.ForeignKey(
        "profiles.ProfileMeta",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    href = models.CharField(max_length=255)
    template_name = models.CharField(max_length=100, null=True, blank=True)
    icon = models.CharField(max_length=255, null=True, blank=True)
    picture = models.ImageField(null=True, blank=True)
    picture_profile_role = models.CharField(max_length=1, null=True, blank=True)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def refresh(self) -> None:
        """
        Refresh the notification instance for profile
        """
        self.seen = False
        self.save()

    def mark_as_read(self) -> None:
        """
        Mark the notification as read
        """
        self.seen = True
        self.save()

    @property
    def picture_url(self) -> str:
        """Generate club picture url"""
        if self.picture:
            return urljoin(settings.BASE_URL, self.picture.url)

    def __str__(self) -> str:
        status = "ODCZYTANO" if self.seen else "NIE ODCZYTANO"
        return (
            f"{self.target} -- {self.title} -- [{status}] -- Update: {self.updated_at}"
        )

    class Meta:
        verbose_name = "Powiadomienia użytkownika"
        verbose_name_plural = "Powiadomienia użytkowników"
