import logging
import operator
from functools import reduce

from app import mixins, utils
from app.mixins import FilterPlayerViewMixin
from clubs.models import Club, League
from clubs.models import LeagueHistory as CLeagueHistory
from clubs.models import Team
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View, generic
from metrics.team import (
    LeagueAdvancedTableRawMetrics,
    LeagueChildrenSerializer,
    LeagueMatchesMetrics,
    LeagueMatchesRawMetrics,
    PlaymakerMetrics,
    SummarySerializer,
)
from profiles.utils import get_datetime_from_age
from roles import definitions
from users.models import User
from utils import get_current_season


logger = logging.getLogger(__name__)


def get_or_make(dataindex, key, method, options, overwrite: bool = False):
    """Caches data in leagueHistorical data, under the Key

    When no data present under key - create new one and save object.

    dataindex represetns LeagueHistory
    key is the name of attribute in .data
    method is the way to generate data
    options are kwargs for given method

    """
    if dataindex.data is not None and key in dataindex.data and not overwrite:
        return dataindex.data[key]
    else:
        if dataindex.data is None:
            dataindex.data = {}
        data = method(*options)

        dataindex.data[key] = data
        dataindex.save()
        return data


class Refresh:
    @classmethod
    def summary(cls, league_history: CLeagueHistory, overwrite: bool = False):
        key = "summary"
        return get_or_make(
            league_history,
            key,
            SummarySerializer.serialize,
            (league_history.league, league_history.season.name),
            overwrite=overwrite
        )

    @classmethod
    def table(cls, league_history: CLeagueHistory, overwrite: bool = False):
        key = "advanced"
        return get_or_make(
            league_history,
            key,
            LeagueAdvancedTableRawMetrics.serialize,
            (league_history.league, league_history),
            overwrite=overwrite
        )

    @classmethod
    def playmakers(cls, league_history: CLeagueHistory, overwrite: bool = False):
        key = "playmakers"
        return get_or_make(
            league_history,
            key,
            PlaymakerMetrics.calc,
            {league_history.league},
            overwrite=overwrite
        )


class ComplexViews(
    generic.TemplateView,
    mixins.PaginateMixin,
    mixins.ViewModalLoadingMixin,
    mixins.ViewFilterMixin,
):
    pass


class PlaysBaseView(ComplexViews):
    http_method_names = ["get"]
    template_name = "plays/plays.html"
    page_title = None
    filter_on = True
    tab = None
    paginate_limit = 15

    def set_kwargs(self, options, slug):
        self.season = self.request.GET.get("season") or get_current_season()
        options["current_season"] = self.season
        options["page_title"] = self.page_title
        options["tab"] = self.tab
        if not slug:
            self.league = None

        else:
            self.league = League.objects.get(slug=slug)
            if self.league.visible == False:
                raise Http404()
    
        options["league"] = self.league

        # filters on
        if self.filter_on:
            options["leagues"] = League.objects.filter(
                parent__isnull=True,
                visible=True
            ).order_by("order")
            history_leagues_all = CLeagueHistory.objects.select_related("league").filter(
                season__name=self.season,
                visible=True
            )
            options["history_leagues"] = history_leagues_all.order_by("league__order")
            options["history_leagues_no_parent"] = history_leagues_all.filter(league__parent__isnull=True).order_by("league__order")
            options["league_parents"] = League.objects.filter(
                league__historical__season__name=self.season,
                isparent=True,
                visible=True
            ).order_by("name", "order").distinct("name")

        else:
            options["leagues"] = None
            options["history_leagues"] = None
        return options

    def get(self, request, slug, *args, **kwargs):
        self.set_kwargs(kwargs, slug)
        return super().get(request, *args, **kwargs)


class PlaysViews(PlaysBaseView):
    """
    Podsumowanie (zgodnie z tym co na flashscore)
        Dzisiejsze mecze (data_game.date = dzis)
        Najświeższe wyniki (ostatnie 12 meczów rozegranych, wg daty)
        Następne (najbliższe 12 meczów, które są do rozegrania)
    """

    page_title = "Rozgrywki"
    tab = "summary"

    def set_kwargs(self, options, slug):
        options = super().set_kwargs(options, slug)

        try:
            data_index = self.league.historical.all().get(season__name=self.season)
        except Exception:
            options["objects"] = {}
            return options

        # options["objects"] = dict(Refresh.summary(data_index))
        data = dict(Refresh.summary(data_index))
        output = {}
        output["Nachodzące mecze"] = {}
        output["Rozegrane mecze"] = {}

        if data.get("today_games"):
            output["Dzisiejsze mecze"] = data.get("today_games") 
        if data.get("current_games"):
            output["Rozegrane mecze"] = data.get("current_games")
        if data.get("next_games"):
            output["Nachodzące mecze"] = data.get("next_games")

        options["objects"] = output

        options["summary_table_objects"] = Refresh.table(data_index)
        # data_index_key = 'summary'
        # if data_index.data is not None and data_index_key in data_index.data:
        #     options['objects'] = data_index.data[data_index_key]
        # else:
        #     if data_index.data is None:
        #         data_index.data = {}

        #     options['objects'] = SummarySerializer.serialize(self.league, self.season)
        #     data_index.data[data_index_key] = options['objects']
        #     data_index.save()
        #print(f'..... {self.season}')
        #print(options["objects"])
    
        return options


class PlaysTableViews(PlaysBaseView):
    tab = "table"
    page_title = "Rozgrywki :: Tabela"

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)
        data_index = self.league.historical.all().get(season__name=self.season)
        try:
            data_index = self.league.historical.all().get(season__name=self.season)
        except Exception:
            options["objects"] = []
            return options
        options["objects"] = Refresh.table(data_index)
        return options


class PlaysPlaymakerViews(PlaysBaseView):
    page_title = "Rozgrywki :: Playmaker.pro"
    tab = "playmaker"
    test_data = {
        "players": [
            {
                "name": "Jacek Jasinski",
                "url": "http://localhost:8000/users/player-rafal-kesik-2/",
            }
        ],
        "coaches": [],
    }

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)

        try:
            data_index = self.league.historical.all().get(season__name=self.season)
        except Exception:
            options["objects"] = []
            return options

        options["objects"] = Refresh.playmakers(data_index)
        return options


class PlaysScoresViews(PlaysBaseView):
    page_title = "Rozgrywki :: Wyniki"
    tab = "scores"

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)
        # if self.league.is_parent:

        #     options['objects'] = dict(LeagueChildrenSerializer().serialize(self.league))
        # else:
        # options['objects'] = dict(LeagueMatchesMetrics().serialize(self.league, self.season, sort_up=True))
        from collections import OrderedDict
        data = dict(
            LeagueMatchesMetrics().serialize(self.league, self.season, sort_up=True)
        )

        data = OrderedDict(sorted(data.items(), reverse=True))
        options["objects"] = {}
        options["objects"]["Wyniki"] = {}
        options["objects"]["Wyniki"] = data
        return options


class PlaysGamesViews(PlaysBaseView):
    """Widok spotkań"""

    page_title = "Rozgrywki :: Spotkania"
    tab = "matches"

    def set_kwargs(self, *args, **kwargs):
        options = super().set_kwargs(*args, **kwargs)

        options["objects"] = {}
        options["objects"]["Mecze"] = {}
        options["objects"]["Mecze"] = dict(
            LeagueMatchesMetrics().serialize(
                self.league, self.season, played=False, sort_up=False
            )
        )
        return options


class PlaysListViews(ComplexViews):
    """Główny widok spotań"""

    template_name = "plays/list.html"
    http_method_names = ["get"]
    paginate_limit = 15
    page_title = "Rozgrywki"
    tab = None

    def get(self, request, *args, **kwargs):
        from plays.models import PlaysConfig

        redirect_league = request.user.profile.get_league_object()

        if redirect_league:
            return redirect("plays:summary", slug=redirect_league.slug)

        plays_config = PlaysConfig.objects.all().first()

        if plays_config:
            league_slug = plays_config.main_league.slug
            return redirect("plays:summary", slug=league_slug)

        else:
            history_league = CLeagueHistory.objects.all().first()
            return redirect("plays:summary", slug=history_league.league.slug)

        leagues = League.objects.filter(parent__isnull=True)
        season = request.GET.get("season") or get_current_season()

        kwargs["objects"] = leagues
        # kwargs['objects'] = dict(LeagueMatchesRawMetrics().serialize(league_obj, '2020/2021'))
        kwargs["page_title"] = self.page_title
        kwargs["current_season"] = season
        kwargs["debug_data"] = kwargs["objects"]
        kwargs["tab"] = self.tab
        return super().get(request, *args, **kwargs)


class RefreshManager:
    @classmethod
    def run(cls, verbose: bool = False, ids: list = None, keyname: str = None):
        from clubs.models import LeagueHistory as CLeagueHistory
        print(f"# Params verbose={verbose} ids={ids} keyname={keyname}")
        keyname = keyname

        if keyname and keyname not in ["future-games", "scores", "playmakers", "summary", "table"]:
            raise RuntimeError(f"Selected `keyname`: {keyname} is not allowed.")
        _all = CLeagueHistory.objects.all()
        if ids:
            _all = _all.filter(id__in=ids)
        print(f"# Selected {_all.count()} for update.")
        for league_history in _all:
            season = league_history.season
            league = league_history.league
            print(f"Refresh stared for {league_history}")
            tasks = {
                "scores": (
                    LeagueMatchesMetrics().serialize,
                    (league, season.name),
                    {"league_history": league_history, "sort_up": True, "overwrite": True}
                ),
                "future-games": (
                    LeagueMatchesMetrics().serialize,
                    (league, season.name),
                    {"league_history": league_history, "sort_up": False, "overwrite": True, "played": False}
                ),
                "playmakers": (Refresh.playmakers, (league_history,), {"overwrite": True}),
                "summary": (Refresh.summary, (league_history,), {"overwrite": True}),
                "table": (Refresh.table, (league_history,), {"overwrite": True}),
            }
            for task, (method, args, kwargs) in tasks.items():
                if keyname:
                    if task != keyname:
                        continue
                print(f"Running data serialization for `{task}`")
                method(*args, **kwargs)
