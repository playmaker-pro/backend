from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api import errors as base_errors
from api.views import EndpointView
from clubs import errors, models, services
from clubs.api import api_filters, serializers

User = get_user_model()


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = models.Team.objects.all().order_by("name")
    serializer_class = serializers.TeamSelect2Serializer

    def get_queryset(self):
        q_name = self.request.query_params.get("q")
        if q_name:
            return self.queryset.filter(name__icontains=q_name)
        return self.queryset


class TeamSearchApi(APIView):
    permission_classes = []

    # @method_decorator(cache_page(60*60*2))
    def get(self, request):
        teams = models.Team.objects.all().order_by("name")

        q_name = request.query_params.get("q")
        if q_name:
            teams = teams.filter(name__icontains=q_name)

        serializer = serializers.TeamSelect2Serializer(
            teams, many=True, context={"request": request}
        )

        return Response({"results": serializer.data})


class TeamHistorySearchApi(APIView):
    permission_classes = []

    def get(self, request):
        teams = (
            models.TeamHistory.objects.select_related("team", "league_history__season")
            .all()
            .order_by("team__name")
        )
        q_name = request.query_params.get("q")
        q_season = request.query_params.get("season")
        if q_name:
            teams = teams.filter(team__name__icontains=q_name)
        if q_season:
            teams = teams.filter(league_history__season__name=q_season)
        serializer = serializers.TeamHistorySelect2Serializer(
            teams[:20], many=True, context={"request": request}
        )

        return Response({"results": serializer.data})


class ClubSearchApi(APIView):
    permission_classes = []

    # @method_decorator(cache_page(60*60*2))
    def get(self, request):
        q_season = request.query_params.get("season")
        if q_season:
            queryset = (
                models.Club.objects.filter(
                    teams__historical__league_history__season__name__in=[q_season]
                )
                .distinct()
                .order_by("name")
            )
        else:
            queryset = models.Club.objects.all()

        q_name = request.query_params.get("q")
        if q_name:
            queryset = queryset.filter(name__icontains=q_name)

        serializer = serializers.ClubSelect2Serializer(
            queryset[:10], many=True, context={"request": request}
        )

        return Response({"results": serializer.data})


class ClubTeamsSearchApi(APIView):
    permission_classes = []
    club_service = services.ClubService()

    def get(self, request) -> Response:
        """
        Get list of teams assigned to given club
        takes ?club_id as param
        """
        club_id: int = request.query_params.get("club_id")
        if not club_id:
            raise base_errors.ParamsRequired(["club_id"])

        if not (club_obj := self.club_service.club_exist(club_id)):  # noqa:  E999
            raise errors.ClubDoesNotExist

        qs = models.Team.objects.filter(club=club_obj)
        serializer = serializers.TeamSerializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ClubTeamsAPI(EndpointView):
    permission_classes = []
    club_service = services.ClubTeamService()

    def get_club_teams(self, request: Request) -> Response:
        """Retrieve filtered clubs and serialize them."""
        filters = request.query_params.dict()
        season: str = filters.get("season")
        gender: str = filters.get("gender")

        if not season:
            raise errors.SeasonParameterMissing
        try:
            self.club_service.validate_gender(gender)
        except (ValueError, AttributeError):
            raise errors.InvalidGender

        club_filter = api_filters.ClubFilter(filters)
        clubs = club_filter.qs
        serializer = serializers.ClubTeamSerializer(
            clubs, many=True, context={"gender": gender, "season": season}
        )
        return Response({"clubs": serializer.data}, status=status.HTTP_200_OK)


class LeagueAPI(EndpointView):
    service = services.LeagueService()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self, highest_only: bool = False, **kwargs) -> QuerySet:
        """Get Leagues queryset"""
        if highest_only:
            qs = self.service.get_highest_parents()
        else:
            qs = self.service.get_leagues()

        return self.filter_queryset(qs, **kwargs)

    def filter_queryset(self, queryset: QuerySet, **kwargs) -> QuerySet:
        """Filter queryset by gender and visible flag"""
        if gender := kwargs.get("gender"):
            queryset = self.service.filter_gender(queryset, gender)

        return queryset.filter(visible=True)

    def get_highest_parents(self, request: Request) -> Response:
        """Get list of leagues (highest parents only)"""

        gender: str = request.query_params.get("gender")
        try:
            self.service.validate_gender(gender)
        except ValueError:
            raise errors.InvalidGender

        qs = self.get_queryset(highest_only=True, gender=gender)
        serializer = serializers.LeagueBaseDataSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SeasonAPI(EndpointView):
    """
    View for listing seasons and filtering them by name.

    Only seasons where `is_in_verify_form` is True are included in the results.

    This view supports additional filtering by providing a 'season' query parameter.
    If the 'season' parameter is provided, the view will return only seasons whose name includes the specified season string.
    Seasons are returned in descending order by their name.

    Example usage: /seasons/?season=2021
    """

    permission_classes = []
    service = services.SeasonService()

    def list_seasons(self, request: Request) -> Response:
        """
        Returns a list of seasons where `is_in_verify_form` is True,
        or a filtered list of such seasons if the 'season' query parameter is provided.

        The seasons are ordered by 'name' in descending order (newest to oldest).
        """
        season = request.GET.get("season", None)

        if season and not self.service.validate_season(season):
            raise errors.InvalidSeasonFormatException()

        # Query only seasons where is_in_verify_form is True
        seasons = models.Season.objects.filter(is_in_verify_form=True)

        # If season query parameter is provided, filter the seasons by name
        if season:
            seasons = seasons.filter(name__icontains=season)

        # Check if the query returned any results
        if not seasons.exists():
            raise errors.SeasonDoesNotExist()

        # Order by 'name' in descending order to return the seasons from newest to oldest
        seasons = seasons.order_by("-name")

        serializer = serializers.SeasonSerializer(seasons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TeamsAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["post", "patch", "get"]

    def get_team(self, request: Request, team_id: int) -> Response:
        # TODO(rkesik) we might turn that into a TeamService but since there is no addtional logic
        # we can keep it as that.
        try:
            team = models.Team.objects.get(id=team_id)
        except Team.Follow.DoesNotExist:
            raise base_errors.ObjectDoesNotExist(details="team does not exists")

        serializer = serializers.TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_team_labels(self, request: Request, team_id: int) -> Response:
        # TODO(rkesik) we might turn that into a TeamService but since there is no addtional logic
        # we can keep it as that.
        try:
            team = models.Team.objects.get(id=team_id)
        except Team.Follow.DoesNotExist:
            raise base_errors.ObjectDoesNotExist(details="team does not exists")

        season_name = request.GET.get("season_name")
        query = {}
        if season_name:
            query = {"season_name": season_name}
        serializer = serializers.TeamLabelsSerializer(
            team.labels.filter(**query), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
