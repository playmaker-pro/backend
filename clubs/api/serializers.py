import typing
import uuid

from rest_framework import serializers

from clubs import models
from external_links.serializers import ExternalLinksSerializer
from profiles.models import TeamContributor
from users.api.serializers import UserDataSerializer
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
        return obj.short_name

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
    picture_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Club
        exclude = (
            "name",
            "scrapper_autocreated",
            "data_mapper_id",
            "autocreated",
        )

    def get_picture_url(self, obj: models.Club) -> typing.Optional[str]:
        """
        Retrieve the absolute url of the club logo.
        """
        request = self.context.get("request")
        try:
            url = request.build_absolute_uri(obj.picture.url)
        except (ValueError, AttributeError):
            return None
        return url


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
        exclude = ("name", "autocreated", "data_mapper_id", "scrapper_autocreated")

    def get_current_team_league_history(self, obj: models.Team) -> dict:
        """Get current, serialized league history of team"""
        return LeagueHistorySerializer(obj.league_history).data


class CustomTeamHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Team model providing customized fields.

    The CustomTeamHistorySerializer is designed to represent the historical data of
    teams, with details about the league a team was part of,
    its division, and some general team information like name and gender.

    The division field can represent an age group for junior teams
    (e.g., "U8", "U11", "U14") or
    a seniority level for senior teams (e.g., "seniorzy").
    """

    division = serializers.SerializerMethodField()
    historical_league_name = serializers.CharField(source="league_history.league.name")
    name = serializers.CharField(source="short_name")
    gender = GenderSerializer()

    class Meta:
        model = models.Team
        fields = [
            "id",
            "name",
            "gender",
            "division",
            "historical_league_name",
        ]

    def get_division(self, obj: models.Team) -> typing.Optional[str]:
        """
        Retrieve the division of a team based on its junior group or seniority.

        For junior teams, the division will represent the age group
        (e.g., "U8", "U11", "U14").
        For senior teams, the division will indicate the seniority level
        (e.g., "seniorzy").
        """
        if obj.junior_group and hasattr(obj.junior_group, "name"):
            return obj.junior_group.name
        elif obj.seniority and hasattr(obj.seniority, "name"):
            return obj.seniority.name
        return None


class ClubTeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="short_name")
    club_teams = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    country_name = serializers.CharField(source="country.name", required=False)

    class Meta:
        model = models.Club
        fields = (
            "id",
            "name",
            "picture_url",
            "country_name",
            "club_teams",
        )

    def get_picture_url(self, obj: models.Club) -> typing.Optional[str]:
        """
        Retrieve the absolute url of the club logo.
        """
        request = self.context.get("request")
        try:
            url = request.build_absolute_uri(obj.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    def get_club_teams(
        self, obj: models.Club
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Retrieve the list of team histories related to a given club.

        This method fetches all the team history records that are related
        to the provided club.
        It can further filter these records based on gender and season context
        provided during serialization.
        """
        season = self.context.get("season")
        gender = self.context.get("gender")

        filters = {"club": obj}

        # Filtering by gender
        if gender:
            if gender.upper() == models.Gender.MALE:
                filters["gender"] = models.Gender.get_male_object().id
            elif gender.upper() == models.Gender.FEMALE:
                filters["gender"] = models.Gender.get_female_object().id

        # Filtering by season
        if season:
            filters["league_history__season__name"] = season

        # Applying filters
        team_histories_qs = (
            models.Team.objects.select_related("league_history", "gender")
            .prefetch_related("junior_group", "seniority", "league_history__league")
            .filter(**filters)
        )
        return CustomTeamHistorySerializer(
            team_histories_qs, many=True, context=self.context
        ).data


class TeamHistorySerializer(serializers.ModelSerializer):
    team = TeamSerializer(required=False)
    league_history = LeagueHistorySerializer(required=False)

    class Meta:
        model = models.Team
        exclude = ("data_mapper_id", "autocreated")


class TeamHistoryBaseProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Team model focused on providing base profile information.

    This serializer extracts the essential information about the team and its
    associated league.
    It provides the team's name and details about the league's entity.
    """

    team_name = serializers.SerializerMethodField()
    league_name = serializers.CharField(source="league.name")
    league_id = serializers.IntegerField(source="league.id")
    team_contributor_id = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    country = serializers.CharField(source="get_country", read_only=True)
    season = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = [
            "id",
            "team_name",
            "league_name",
            "league_id",
            "team_contributor_id",
            "picture_url",
            "country",
            "season",
        ]

    def get_team_name(self, obj: models.Team) -> str:
        """
        Retrieve the team's short name if available; otherwise, return the
        team's full name.
        """
        return obj.short_name or obj.name

    def get_picture_url(self, obj: models.Team) -> typing.Optional[str]:
        """
        Retrieve the absolute url of the club logo.
        """
        request = self.context.get("request")
        try:
            url = request.build_absolute_uri(obj.club.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    @staticmethod
    def get_season(obj: models.Team) -> typing.Optional[str]:
        """
        Retrieve the season name associated with the Team instance.
        """
        team_history_season = getattr(obj, "league_history__season", None)
        if team_history_season:
            return team_history_season.name

        league_history_season = getattr(obj.league_history, "season", None)
        if league_history_season:
            return league_history_season.name

    def get_team_contributor_id(
        self,
        obj: models.Team,
    ) -> typing.Optional[int]:
        """
        Retrieve the ID of the primary TeamContributor associated with the given
        Team object.
        """
        profile_uuid: typing.Optional[uuid.UUID] = self.context.get("profile_uuid")
        primary_contributor: typing.Optional[
            TeamContributor
        ] = obj.teamcontributor_set.filter(
            is_primary=True, profile_uuid=profile_uuid
        ).first()

        return primary_contributor.id if primary_contributor else None


class LabelSerializer(serializers.Serializer):
    label_name = serializers.CharField(
        source="label_definition.label_name", max_length=25
    )
    label_description = serializers.CharField(
        source="label_definition.label_description", max_length=200
    )
    season_name = serializers.CharField(max_length=9)
    icon = serializers.CharField(source="label_definition.icon", max_length=200)
    league = serializers.CharField(max_length=255, required=False)
    team = serializers.CharField(max_length=255, required=False)
    season_round = serializers.CharField(max_length=10, required=False)


class TeamLabelsSerializer(LabelSerializer):
    pass


class ClubLabelsSerializer(LabelSerializer):
    pass
