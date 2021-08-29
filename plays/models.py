from django.db import models
from clubs.models import League


class PlaysConfig(models.Model):
    main_league = models.ForeignKey(
        League,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
