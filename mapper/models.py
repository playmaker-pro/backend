from typing import Union, List

import django.core.exceptions
from django.db import models


class Mapper(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_entity(self, **kwargs) -> Union["MapperEntity", None]:
        try:
            return MapperEntity.objects.get(target=self, **kwargs)
        except django.core.exceptions.ObjectDoesNotExist:
            pass

    def get_entities(self) -> List[Union["MapperEntity", None]]:
        return MapperEntity.objects.filter(target=self)

    @property
    def has_entities(self) -> bool:
        return bool(self.get_entities())


class MapperSource(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class MapperEntity(models.Model):

    RELATED_MODELS = (
        ("team", "team"),
        ("player", "player profile"),
        ("coach", "coach profile"),
        ("club", "club"),
        ("team history", "team history"),
        ("league", "league history highest parent"),
        ("play", "league history"),
    )

    DATA_SOURCES = (
        ("scrapper_mongodb", "scrapper_mongodb"),
        ("s38", "s38"),
        ("external", "external"),
        ("xlsx", "xlsx"),
    )

    target = models.ForeignKey(Mapper, on_delete=models.CASCADE)
    mapper_id = models.CharField(max_length=100, null=True, blank=True)
    source = models.ForeignKey(MapperSource, on_delete=models.CASCADE)
    url = models.URLField(max_length=500, null=True, blank=True)
    related_type = models.CharField(max_length=100, choices=RELATED_MODELS)
    database_source = models.CharField(max_length=100, choices=DATA_SOURCES)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.source.name

    class Meta:
        unique_together = ("target", "related_type", "database_source")
