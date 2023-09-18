from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Label(models.Model):
    label_name = models.CharField(max_length=25)
    label_description = models.TextField(null=True, blank=True)
    season_name = models.CharField(max_length=9)
    icon = models.CharField(max_length=200, null=False, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    conditions = models.TextField(null=True, blank=True)
    visible = models.BooleanField(default=True)

    visible_on_profile = models.BooleanField(default=True)
    visible_on_base = models.BooleanField(default=True)
    visible_on_main_page = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label_name} ({self.season_name})"

    class Meta:
        unique_together = ("object_id", "label_name", "season_name")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
