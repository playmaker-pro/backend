from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic

from clubs.models import Club, Team
from users.models import User
from django.core.paginator import Paginator


TABLE_TYPE_PLAYER = 'P'
TABLE_TYPE_TEAM = 'C'
TABLE_TYPE_COACH = 'T'


class TableView(generic.TemplateView):
    template_name = "soccerbase/tables/table.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None

    def get_queryset(self):
        return []

    def get(self, request, *args, **kwargs):
        data = self.get_queryset()
        paginator = Paginator(data, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs["type"] = self.table_type
        return super().get(request, *args, **kwargs)


class PlayersTable(TableView):
    table_type = TABLE_TYPE_PLAYER

    def get_queryset(self):
        return User.objects.filter(declared_role='P')


class TeamsTable(TableView):
    table_type = TABLE_TYPE_TEAM

    def get_queryset(self):
        return Team.objects.all()


class CoachesTable(TableView):
    table_type = TABLE_TYPE_COACH

    def get_queryset(self):
        return User.objects.filter(declared_role='T')
