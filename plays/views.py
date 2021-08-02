from django.db.models import F
from app import mixins, utils

from clubs.models import Club, Team
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from profiles.utils import get_datetime_from_age
from roles import definitions
from users.models import User
import operator
from functools import reduce
from django.db.models import Q, Value
from app.mixins import FilterPlayerViewMixin
from django.utils import timezone

from clubs.models import League
from utils import get_current_season


class PlaysViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    template_name = "plays/plays.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = "Rozgrywki"

    def get(self, request, slug, *args, **kwargs):
        kwargs["data"] = []
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = get_current_season()
        league_obj =League.objects.get(slug=slug)
        kwargs["league"] = league_obj
        kwargs["name"] = league_obj.name
        return super().get(request, *args, **kwargs)


class PlaysScoresViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    template_name = "plays/plays.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = "Rozgrywki :: Wyniki"

    def get(self, request, slug, *args, **kwargs):
        kwargs["objects"] = [
            {
                "name": "Kolejka 30",
                "games": [
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Sokół I",
                        "guest": "Lechia Dzierżoniów",
                        "score": "2 - 1",
                        "date": "10.05 21:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Belchatów",
                        "guest": "Arsenal",
                        "score": "2 - 1",
                        "date": "08.05 19:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Bielawa",
                        "guest": "Bukowa",
                        "score": "2 - 1",
                        "date": "05.05 21:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Sokół I",
                        "guest": "Barcelona",
                        "score": "2 - 1",
                        "date": "05.05 21:00",
                    },
                ],
            },
            {
                "name": "Kolejka 29",
                "games": [
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/url",
                        "host": "Sokół I",
                        "guest": "Lechia Dzierżoniów",
                        "score": "2 - 1",
                        "date": "10.05 21:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Belchatów",
                        "guest": "Arsenal",
                        "score": "2 - 1",
                        "date": "08.05 19:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/url",
                        "host": "Bielawa",
                        "guest": "Bukowa",
                        "score": "2 - 1",
                        "date": "05.05 21:00",
                    },
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/url",
                        "host": "Sokół I",
                        "guest": "Barcelona",
                        "score": "2 - 1",
                        "date": "05.05 21:00",
                    },
                ],
            },
        ]
        from metrics.team import LeagueMatchesMetrics
        league_obj = League.objects.get(slug=slug)
        kwargs['objects'] = dict(LeagueMatchesMetrics().serialize(league_obj, '2013/2014'))
        print(kwargs['objects'])
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = get_current_season()
        
        kwargs["league"] = league_obj
        kwargs["name"] = league_obj.name
        return super().get(request, *args, **kwargs)


class PlaysTableViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    template_name = "plays/plays.html"
    http_method_names = ["get"]
    paginate_limit = 15
    tab = "table"
    table_type = None
    page_title = "Rozgrywki :: Wyniki"

    def get(self, request, slug, *args, **kwargs):
        kwargs["tab"] = self.tab
        kwargs["objects"] = [
            {
                "position": "1",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Manchaster",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "P", "P", "R"],
            },
            {
                "position": "2",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Lechia Dzierżoniów",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "R", "R", "R"],
            },
            {
                "position": "3",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Bukowa Chata",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "77:44",
                "points": 42,
                "trend": ["L", "L", "W", "W", "R", "R", "R"],
            },
            {
                "position": "4",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Lechia Dzierżoniów",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "R", "R", "R"],
            },
            {
                "position": "5",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Lechia Dzierżoniów",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "R", "R", "R"],
            },
            {
                "position": "6",
                "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                "team": "Lechia Dzierżoniów",
                "games": 23,
                "wins": 2,
                "losts": 21,
                "draws": 0,
                "goals": "23:44",
                "points": 42,
                "trend": ["W", "L", "W", "W", "R", "R", "R"],
            },
        ]
        
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = get_current_season()
        league_obj = League.objects.get(slug=slug)
        kwargs["league"] = league_obj
        kwargs["name"] = league_obj.name
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class PlaysPlaymakerViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    template_name = "plays/plays.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = "Rozgrywki :: Spotkania"
    tab = "playmaker"

    def get(self, request, slug, *args, **kwargs):
        kwargs["objects"] = {
            "players": [
                {
                    "name": "Jacek Jasinski",
                    "url": "http://localhost:8000/users/player-rafal-kesik-2/",
                }
            ],
            "coaches": [],
        }
        kwargs["tab"] = self.tab

        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = get_current_season()
        
        league_obj =League.objects.get(slug=slug)
        kwargs["league"] = league_obj
        kwargs["name"] = league_obj.name
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)


class PlaysGamesViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    template_name = "plays/plays.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = "Rozgrywki :: Playmaker"

    def get(self, request, slug, *args, **kwargs):
        kwargs["objects"] = []
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = get_current_season()
        league_obj =League.objects.get(slug=slug)
        kwargs["league"] = league_obj
        kwargs["name"] = league_obj.name
        return super().get(request, *args, **kwargs)
