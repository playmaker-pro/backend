from rest_framework import serializers
from clubs import models


class TeamSelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj: models.Team) -> str:
        return obj.name_with_league_full

    class Meta:
        model = models.Team
        fields = [
            "id",
            "text",
        ]


class TeamHistorySelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj: models.TeamHistory) -> str:
        return f"{obj.team}"

    class Meta:
        model = models.TeamHistory
        fields = [
            "id",
            "text",
        ]


class ClubSelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj.name

    class Meta:
        model = models.Club
        fields = [
            "id",
            "text",
        ]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Season
        fields = "__all__"


class LeagueSerializer(serializers.ModelSerializer):
    data_seasons = SeasonSerializer(many=True)

    class Meta:
        model = models.League
        fields = "__all__"
