from rest_framework import serializers
from . import models


class ExternalLinksEntitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="source.name")

    class Meta:
        model = models.ExternalLinksEntity
        fields = ("id", "source", "url", "name")


class ExternalLinksSerializer(serializers.ModelSerializer):
    links = ExternalLinksEntitySerializer(many=True)

    class Meta:
        model = models.ExternalLinks
        fields = ("links",)
