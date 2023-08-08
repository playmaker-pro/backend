from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.request import Request
from api.views import EndpointView
from clubs.models import Club, Team, TeamHistory
from . import serializers
from clubs import services, errors

User = get_user_model()


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Team.objects.all().order_by("name")
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
        teams = Team.objects.all().order_by("name")

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
            TeamHistory.objects.select_related("team", "league_history__season")
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
                Club.objects.filter(
                    teams__historical__league_history__season__name__in=[q_season]
                )
                .distinct()
                .order_by("name")
            )
        else:
            queryset = Club.objects.all()

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

        if not (club_obj := self.club_service.club_exist(club_id)):
            raise errors.ClubDoesNotExist

        qs = Team.objects.filter(club=club_obj)
        serializer = serializers.TeamSerializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LeagueAPI(EndpointView):
    service = services.LeagueService()

    def get_highest_parents(self, request: Request) -> Response:
        """Get list of leagues (highest parents only)"""
        qs = self.service.get_highest_parents()
        serializer = serializers.LeagueSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
