from django.db import models
from django.db.models.functions import Coalesce


class LeagueManager(models.Manager):
    def is_top_parent(self):
        return self.filter(parent__isnull=True, isparent=True, visible=True)
