from rest_framework.views import APIView
from clubs.models import Team, Club
from rest_framework import viewsets
from .serizalizer import TeamSerializer, ClubSerializer

from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

User = get_user_model()


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSerializer

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

        serializer = TeamSerializer(teams, many=True, context={"request": request})

        return Response({"results": serializer.data})


class ClubSearchApi(APIView):
    permission_classes = []

    # @method_decorator(cache_page(60*60*2))
    def get(self, request):
        queryset = Club.objects.all().order_by("name")

        q_season = request.query_params.get("season")
        if q_season:
            queryset = Club.objects.filter(teams__historical__season__name__in=[q_season]).order_by("name")

        q_name = request.query_params.get("q")
        if q_name:
            queryset = queryset.filter(name__icontains=q_name)

        serializer = ClubSerializer(queryset, many=True, context={"request": request})

        return Response({"results": serializer.data})
