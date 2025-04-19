from django.db import models

# class Notification: ...


class Notification(models.Model):
    profile = models.ForeignKey(
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

    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def refresh(self) -> None:
        """
        Refresh the notification instance for profile
        """
        self.seen = False
        self.save()

    def __str__(self) -> str:
        return f"{self.profile} -- {self.title} -- [{'ODCZYTANO' if self.seen else 'NIE ODCZYTANO'}] -- Update: {self.updated_at}"

    class Meta:
        verbose_name = "Powiadomienia użytkownika"
        verbose_name_plural = "Powiadomienia użytkowników"
        verbose_name_plural = "Powiadomienia użytkowników"
        verbose_name_plural = "Powiadomienia użytkowników"
