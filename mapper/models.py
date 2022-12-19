from typing import Union

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


class MapperSource(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class MapperEntity(models.Model):
    target = models.ForeignKey(Mapper, on_delete=models.CASCADE)
    mapper_id = models.CharField(max_length=100, null=True, blank=True)
    source = models.ForeignKey(MapperSource, on_delete=models.CASCADE)
    url = models.URLField(max_length=300, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.source.name

    class Meta:
        unique_together = ("target", "source")
