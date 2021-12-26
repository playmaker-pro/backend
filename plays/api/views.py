from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.db.models import F, Q, Value
from clubs.models import League
from utils import get_current_season


class LeagueMenuSerializer():
    pass

class LeagueMenu(APIView):

    def get(self, request):
        season_name = request.GET.get("season") or get_current_season()
        leagues = League.objects.filter(visible=True).filter(
                Q(
                    Q(isparent=True) |
                    Q(parent__isnull=True)
                )
                & 
                Q(
                    Q(
                        Q(historical__season__name=season_name) &
                        Q(historical__visible=True)
                    )
                    |
                    Q( 
                        Q(childs__historical__season__name=season_name) &
                        Q(childs__historical__visible=True)
                    )
                )
            ).order_by("order").distinct()
        data = LeagueMenuSerializer(leagues, many=True).data
        return Response(data)