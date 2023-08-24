from rest_framework import serializers

from clubs import models
from external_links.serializers import ExternalLinksSerializer
from users.serializers import UserDataSerializer
from voivodeships.serializers import VoivodeshipSerializer


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


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Gender
        fields = "__all__"


class SenioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Seniority
        fields = "__all__"


class JuniorAgeGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JuniorAgeGroup
        fields = "__all__"


class LeagueSerializer(serializers.ModelSerializer):
    data_seasons = SeasonSerializer(many=True, required=False)
    gender = GenderSerializer(required=False)
    seniority = SenioritySerializer(required=False)
    name = serializers.CharField(source="get_upper_parent_names", read_only=True)

    class Meta:
        model = models.League
        exclude = ("scrapper_autocreated",)


class LeagueBaseDataSerializer(LeagueSerializer):
    """League serializer with limited fields"""

    class Meta(LeagueSerializer.Meta):
        exclude = ()
        fields = ["id", "name", "gender", "seniority"]


class LeagueHistorySerializer(serializers.ModelSerializer):
    season = SeasonSerializer(required=False)
    league = LeagueBaseDataSerializer(required=False)

    class Meta:
        model = models.LeagueHistory
        fields = "__all__"


class ClubSerializer(serializers.ModelSerializer):
    voivodeship_obj = VoivodeshipSerializer(required=False)
    manager = UserDataSerializer(required=False)
    editors = UserDataSerializer(many=True, required=False)
    stadion_address = serializers.CharField(required=False)
    practice_stadion_address = serializers.CharField(required=False)

    class Meta:
        model = models.Club
        exclude = (
            "scrapper_autocreated",
            "data_mapper_id",
            "autocreated",
        )


class TeamSerializer(serializers.ModelSerializer):
    club = ClubSerializer(required=False)
    gender = GenderSerializer(required=False)
    seniority = SenioritySerializer(required=False)
    junior_group = JuniorAgeGroupSerializer(required=False)
    manager = UserDataSerializer(required=False)
    league = LeagueSerializer(required=False)
    editors = UserDataSerializer(many=True, required=False)
    external_links = ExternalLinksSerializer(required=False)
    current_team_league_history = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        exclude = ("autocreated", "data_mapper_id", "scrapper_autocreated")

    def get_current_team_league_history(self, obj: models.Team) -> dict:
        """Get current, serialized league history of team"""
        if latest_th := obj.get_latest_team_history():
            return LeagueHistorySerializer(latest_th.league_history).data


class TeamHistorySerializer(serializers.ModelSerializer):
    team = TeamSerializer(required=False)
    league_history = LeagueHistorySerializer(required=False)

    class Meta:
        model = models.TeamHistory
        exclude = ("data_mapper_id", "autocreated")
