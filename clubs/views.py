from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic

from . import models


class ClubShow(generic.TemplateView):
    template_name = "clubs/show_club.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug:
            club = get_object_or_404(models.Club, slug=slug)
            user = self.request.user

        kwargs["club"] = club

        return super().get(request, *args, **kwargs)


class TeamShow(generic.TemplateView):
    template_name = "clubs/show_team.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug:
            team = get_object_or_404(models.Team, slug=slug)
            user = self.request.user

        kwargs["team"] = team

        return super().get(request, *args, **kwargs)
