from django.db import models
from django.conf import settings


class PremiumRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription = models.BooleanField(default=False)
    service = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if exists := PremiumRequest.objects.filter(user=self.user).first():
            exists.delete()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.user} (subscription: {self.subscription}, service: {self.service})"
        )
