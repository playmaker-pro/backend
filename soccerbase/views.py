from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic

from clubs.models import Club, Team
from users.models import User


class PlayersTable(generic.TemplateView):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        players = User.objects.filter(declared_role='P')

        kwargs["objects"] = players
        kwargs["type"] = 'P'
        return super().get(request, *args, **kwargs)


class TeamsTable(generic.TemplateView):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        clubs = Club.objects.all()
        user = self.request.user

        kwargs["objects"] = clubs
        kwargs["type"] = 'C'

        return super().get(request, *args, **kwargs)


class CoachesTable(generic.TemplateView):
    template_name = "soccerbase/table.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        coaches = User.objects.filter(declared_role='T')
        kwargs["objects"] = coaches
        kwargs["type"] = 'T'
        return super().get(request, *args, **kwargs)
