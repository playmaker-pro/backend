from rest_framework import serializers
from . import models


class PlayerProfilePositionSerializer(serializers.ModelSerializer):
    position_name = serializers.CharField(source="player_position.name", read_only=True)

    class Meta:
        model = models.PlayerProfilePosition
        fields = ["player_position", "position_name", "is_main"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {"player_position": ret["player_position"], "is_main": ret["is_main"]}


class PlayerVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlayerVideo
        fields = "__all__"


class PlayerMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlayerMetrics
        fields = "__all__"


class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LicenceType
        fields = "__all__"


class CoachLicenceSerializer(serializers.ModelSerializer):
    licence = LicenceSerializer()

    class Meta:
        model = models.CoachLicence
        fields = "__all__"
