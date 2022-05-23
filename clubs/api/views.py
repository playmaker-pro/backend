from rest_framework.views import APIView
from clubs.models import Team
from rest_framework import viewsets
from .serizalizer import TeamSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Team.objects.all().order_by('name')
    serializer_class = TeamSerializer

    def get_queryset(self):

        q_name = self.request.query_params.get('q')
        if q_name:
            return self.queryset.filter(name__icontains=q_name)
        return self.queryset


class TeamSearchApi(APIView):
    permission_classes = []

    def get(self, request):
        teams = Team.objects.all().order_by('name')
        q_name = request.query_params.get('q')
        if q_name:
            teams = teams.filter(name__icontains=q_name)
    
        serializer = TeamSerializer(teams, many=True)
        return Response({'results': serializer.data})
