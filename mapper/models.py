from typing import List, Union

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
    class MapperRelatedModel(models.TextChoices):
        TEAM = "team", "team"
        PLAYER = "player", "player profile"
        COACH = "coach", "coach profile"
        CLUB = "club", "club"
        TEAM_HISTORY = "team history", "team history"
        LEAGUE = "league", "league history highest parent"
        PLAY = "play", "league history"

    class MapperDataSource(models.TextChoices):
        MONGODB = "scrapper_mongodb", "scrapper_mongodb"
        S38 = "s38", "s38"
        EXTERNAL = "external", "external"
        XLSX = "xlsx", "xlsx"

    target = models.ForeignKey(Mapper, on_delete=models.SET_NULL, null=True, blank=True)
    mapper_id = models.CharField(max_length=100, null=True, blank=True)
    source = models.ForeignKey(
        MapperSource, on_delete=models.SET_NULL, null=True, blank=True
    )
    url = models.URLField(max_length=500, null=True, blank=True)
    related_type = models.CharField(max_length=100, choices=MapperRelatedModel.choices)
    database_source = models.CharField(max_length=100, choices=MapperDataSource.choices)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.source.name

    class Meta:
        unique_together = ("target", "related_type", "database_source")
