from rest_framework import serializers

from features.models import NewFeatureSubscription


class FutureFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewFeatureSubscription
        fields = "__all__"
