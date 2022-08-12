from rest_framework.views import APIView
from clubs.models import Team, Club, TeamHistory
from rest_framework import viewsets
from .serizalizer import (
    TeamSelect2Serializer,
    ClubSelect2Serializer,
    TeamHistorySelect2Serializer,
)

from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

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
            TeamHistory.objects.select_related("team", "season")
            .all()
            .order_by("team__name")
        )
        q_name = request.query_params.get("q")
        q_season = request.query_params.get("season")
        if q_name:
            teams = teams.filter(team__name__icontains=q_name)
        if q_season:
            teams = teams.filter(season__name=q_season)
        serializer = TeamHistorySelect2Serializer(
            teams, many=True, context={"request": request}
        )

        return Response({"results": serializer.data})


class ClubSearchApi(APIView):
    permission_classes = []

    # @method_decorator(cache_page(60*60*2))
    def get(self, request):
        q_season = request.query_params.get("season")

        queryset = Club.objects.filter(teams__historical__season__name__in=[q_season]).order_by("name")

        q_name = request.query_params.get("q")
        if q_name:
            queryset = queryset.filter(name__icontains=q_name)

        serializer = ClubSelect2Serializer(
            queryset, many=True, context={"request": request}
        )

        return Response({"results": serializer.data})
