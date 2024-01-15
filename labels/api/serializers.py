from rest_framework import serializers

from labels import models


class LabelDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LabelDefinition
        fields = "__all__"
