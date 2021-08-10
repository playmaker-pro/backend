from django.db.models import F
from app import mixins, utils

from metrics.team import LeagueMatchesMetrics, LeagueChildrenSerializer, LeagueMatchesRawMetrics

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
from metrics.team import SummarySerializer


class ComplexViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin):
    pass


class PlaysBaseView(ComplexViews):
    http_method_names = ["get"]
    template_name = "plays/plays.html"
    page_title = None
    filter_on = True
    tab = None
    paginate_limit = 15

    def set_kwargs(self, options, slug):
        self.season = self.request.GET.get('season') or get_current_season()
        options["current_season"] = self.season
        options["page_title"] = self.page_title

        options['tab'] = self.tab
        if not slug:
            self.league = None

        else:
            self.league = League.objects.get(slug=slug)
        options["league"] = self.league

        # filters on
        if self.filter_on:
            options["leagues"] = League.objects.filter(
                #parent__isnull=True,
                visible=True
            )
        else:
            options['leagues'] = None
        return options

    def get(self, request, slug, *args, **kwargs):
        self.set_kwargs(kwargs, slug)
        return super().get(request, *args, **kwargs)


class PlaysViews(PlaysBaseView):
    '''
    Podsumowanie (zgodnie z tym co na flashscore)
        Dzisiejsze mecze (data_game.date = dzis)
        Najświeższe wyniki (ostatnie 12 meczów rozegranych, wg daty)
        Następne (najbliższe 12 meczów, które są do rozegrania)
    '''
    page_title = "Rozgrywki"
    tab = 'summary'

    def set_kwargs(self, options, slug):
        options = super().set_kwargs(options, slug)
        data_index = self.league.historical.all().get(season__name=self.season)
        data_index_key = 'summary'
        if data_index.data is not None and data_index_key in data_index.data:
            options['objects'] = data_index.data[data_index_key]
        else:
            if data_index.data is None:
                data_index.data = {}

            options['objects'] = SummarySerializer.serialize(self.league, self.season)
            data_index.data[data_index_key] = options['objects']
            data_index.save()

        return options


class PlaysTableViews(PlaysBaseView):
    tab = "table"
    page_title = "Rozgrywki :: Tabela"

    def set_kwargs(self, *args, **kwargs):
        from metrics.team import LeagueAdvancedTableRawMetrics

        options = super().set_kwargs(*args, **kwargs)
        data_index = self.league.historical.all().get(season__name=self.season)

        # @todo: add date check
        data_index_key = 'advanced'
        if data_index.data is not None and data_index_key in data_index.data:
            options['objects'] = data_index.data[data_index_key]
        else:
            if data_index.data is None:
                data_index.data = {}

            options['objects'] = LeagueAdvancedTableRawMetrics.serialize(self.league, data_index)
            data_index.data[data_index_key] = options['objects'] 
            data_index.save()
        return options  
 

class PlaysPlaymakerViews(PlaysBaseView):
    page_title = "Rozgrywki :: Spotkania"
    tab = "playmaker"

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)
        options["objects"] = {
            "players": [
                {
                    "name": "Jacek Jasinski",
                    "url": "http://localhost:8000/users/player-rafal-kesik-2/",
                }
            ],
            "coaches": [],
        }
        return options


class PlaysScoresViews(PlaysBaseView):
    page_title = "Rozgrywki :: Wyniki"
    tab = 'scores'

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)
        if self.league.is_parent:

            options['objects'] = dict(LeagueChildrenSerializer().serialize(self.league))
        else:
            options['objects'] = dict(LeagueMatchesMetrics().serialize(self.league, self.season))
        return options


class PlaysGamesViews(PlaysBaseView):
    '''Widok spotkań'''
    page_title = "Rozgrywki :: Spotkania"
    tab = 'matches'

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)
        if self.league.is_parent:
            raise RuntimeError('tego nie powinno byc')
            options['objects'] = dict(
                LeagueChildrenSerializer().serialize(self.league)
            )
        else:

            options['objects'] = dict(
                LeagueMatchesMetrics().serialize(self.league, self.season, played=False, sort_up=False)
            )
        return options


class PlaysListViews(ComplexViews):
    '''Widok spotkań'''
    template_name = "plays/list.html"
    http_method_names = ["get"]
    paginate_limit = 15
    page_title = "Rozgrywki"
    tab = None

    def get(self, request, *args, **kwargs):
        leagues = League.objects.filter(parent__isnull=True)
        season = request.GET.get('season') or get_current_season()

        kwargs['objects'] = leagues
        # kwargs['objects'] = dict(LeagueMatchesRawMetrics().serialize(league_obj, '2020/2021'))
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = season
        kwargs['debug_data'] = kwargs['objects']
        kwargs['tab'] = self.tab
        return super().get(request, *args, **kwargs)

    def serialize(self, leagues):
        pass