from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Label(models.Model):
    label_name = models.CharField(max_length=25)
    label_description = models.TextField(null=True, blank=True)
    season_name = models.CharField(max_length=9)
    icon = models.CharField(max_length=200)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.label_name} ({self.season_name})"

    class Meta:
        unique_together = ("label_name", "season_name")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
