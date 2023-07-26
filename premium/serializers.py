from rest_framework import serializers
from . import models


class PremiumRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PremiumRequest
        fields = "__all__"
