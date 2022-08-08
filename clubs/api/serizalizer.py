from clubs.models import Team, Club, TeamHistory
from rest_framework import serializers


class TeamSelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj: Team) -> str:
        return obj.full_name or obj.name

    class Meta:
        model = Team
        fields = [
            "id",
            "text",
        ]


class TeamHistorySelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj: TeamHistory) -> str:
        return obj.team.full_name or obj.team.name

    class Meta:
        model = TeamHistory
        fields = [
            "id",
            "text",
        ]


class ClubSelect2Serializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj.name

    class Meta:
        model = Club
        fields = [
            "id",
            "text",
        ]
