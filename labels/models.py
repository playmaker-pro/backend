from enum import Enum as _Enum
from typing import List

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class LabelDefinition(models.Model):
    class LabelNames(str, _Enum):
        YOUTH = "YOUTH"
        HIGH_KEEPER = "HIGH_KEEPER"
        LICENCE_PRO = "LICENCE_PRO"
        LICENCE_A = "LICENCE_A"
        COACH_AGE_30 = "COACH_AGE_30"
        COACH_AGE_40 = "COACH_AGE_40"

    label_name = models.CharField(max_length=25, unique=True)
    label_description = models.TextField(blank=True, null=True)
    catalog_name = models.CharField(max_length=255, null=True)
    icon = models.CharField(max_length=200, blank=True, null=False)
    conditions = models.TextField(blank=True)

    def __str__(self):
        return self.label_name

    @staticmethod
    def get_label_choices() -> List[str]:
        """
        Retrieves a list of all label names defined in the LabelDefinition model.
        """
        return LabelDefinition.objects.all().values_list("label_name", flat=True)


class Label(models.Model):
    label_definition = models.ForeignKey(
        LabelDefinition, on_delete=models.CASCADE, null=True, related_name="labels"
    )
    season_name = models.CharField(max_length=9, null=True, blank=True)

    league = models.CharField(max_length=255, blank=True, null=True)
    team = models.CharField(max_length=255, blank=True, null=True)
    season_round = models.CharField(max_length=10, blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    visible = models.BooleanField(default=True)

    visible_on_profile = models.BooleanField(default=True)
    visible_on_base = models.BooleanField(default=True)
    visible_on_main_page = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label_definition.label_name} ({self.season_name})"

    class Meta:
        unique_together = ("object_id", "label_definition", "season_name")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
