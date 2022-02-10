from django.db import models
from django.db.models import Q


class LeagueManager(models.Manager):
    def is_top_parent(self):
        return self.filter(
            Q(visible=True) & Q(
            parent__isnull=True)
        )
