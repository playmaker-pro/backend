from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from clubs.models import Club, Team, TeamHistory

from .serizalizer import (
    ClubSelect2Serializer,
    TeamHistorySelect2Serializer,
    TeamSelect2Serializer,
)

User = get_user_model()


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSelect2Serializer

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

        serializer = TeamSelect2Serializer(
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
        serializer = TeamHistorySelect2Serializer(
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

        serializer = ClubSelect2Serializer(
            queryset[:10], many=True, context={"request": request}
        )

        return Response({"results": serializer.data})


class ClubTeamsSearchApi(APIView):
    def get(self, request) -> Response:
        # TODO(bartnyk): create logic for getting teams of given club
        return Response({}, status=status.HTTP_200_OK)
