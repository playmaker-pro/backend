import typing

from django.db.models.query import QuerySet
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
    picture_url = serializers.CharField()

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
        if latest_th := obj.get_latest_team_history():  # noqa: E999
            return LeagueHistorySerializer(latest_th.league_history).data


class CustomTeamSerializer(serializers.ModelSerializer):
    """
    Custom Serializer for the Team model.

    This serializer extends the default TeamSerializer to include information about a team's historical leagues.
    While the main TeamSerializer provides standard information about a team, there are cases where more
    contextual information regarding a team's history in various leagues is required.
    Specifically, this serializer is useful when needing to show which highest parent league a team was part
    of during a specific season.

    Note:
    The 'historical_league_names' field requires the 'season' to be provided in the context when serializing.
    If no season is provided, it defaults to fetching the highest parent league from the first historical entry.
    """

    historical_league_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = ["id", "name", "gender", "historical_league_name"]

    def get_historical_league_name(self, obj: models.Team) -> typing.Optional[str]:
        """
        Retrieve the historical league data based on the season context.
        If no season is provided in the context, fetches the first historical entry for the team.
        """
        season = self.context.get("season")
        if season:
            historical_entry: typing.Optional[
                models.TeamHistory
            ] = obj.historical.filter(league_history__season__name=season).first()
        else:
            historical_entry = obj.historical.first()

        return (
            historical_entry.league_history.league.get_highest_parent().name
            if historical_entry
            else None
        )


class ClubTeamSerializer(serializers.ModelSerializer):
    club_teams = serializers.SerializerMethodField()

    class Meta:
        model = models.Club
        fields = ("id", "name", "club_teams")

    def get_club_teams(
        self, obj: models.Club
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Fetch team data for a club based on the gender and season context.
        """
        season = self.context.get("season")
        gender = self.context.get("gender")

        # Filter teams by gender
        teams: QuerySet[models.Team] = obj.teams.all()
        if gender:
            if gender.upper() == models.Gender.MALE:
                teams = teams.filter(gender=models.Gender.get_male_object())
            elif gender.upper() == models.Gender.FEMALE:
                teams = teams.filter(gender=models.Gender.get_female_object())

        return CustomTeamSerializer(
            teams, many=True, context={"gender": gender, "season": season}
        ).data


class TeamHistorySerializer(serializers.ModelSerializer):
    team = TeamSerializer(required=False)
    league_history = LeagueHistorySerializer(required=False)

    class Meta:
        model = models.TeamHistory
        exclude = ("data_mapper_id", "autocreated")


class TeamLabelsSerializer(serializers.Serializer):
    label_name = serializers.CharField(max_length=25)
    label_description = serializers.CharField(max_length=200)
    season_name = serializers.CharField(max_length=9)
    icon = serializers.CharField(max_length=200)
