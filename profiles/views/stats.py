
import logging
from typing_extensions import runtime

from app import mixins
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views import generic
from utils import get_current_season

from stats import adapters, utilites

from .base import SlugyViewMixin

User = get_user_model()


logger = logging.getLogger(__name__)


class ProfileStatsPageView(generic.TemplateView, SlugyViewMixin,  mixins.ViewModalLoadingMixin):
    page_title = None
    template_name = None
    http_method_names = ["get"]
    paginate_limit = 15

    @property
    def season_name(self):
        if settings.FORCED_SEASON_NAME:
            return settings.FORCED_SEASON_NAME
        else:
            return get_current_season()

    def get(self, request, *args, **kwargs):
        user = self.select_user_to_show()
        season_name = get_current_season()

        if self._is_owner(user):
            kwargs["editable"] = True
        kwargs['season_name'] = season_name
        kwargs['show_user'] = user
        kwargs['page_obj'] = self.dispatch_get_or_calculate(user)
        kwargs['page_title'] = self.page_title
        kwargs['modals'] = self.modal_activity(request.user)
        return super().get(request, *args, **kwargs)

    def dispatch_get_or_calculate(self, user):
        if user.is_player or user.is_coach:
            return self.get_data_or_calculate(user)
        else:
            return self._empty_data()

    def get_data_or_calculate(self, *args, **kwargs):
        return self._empty_data()

    def _empty_data(self):
        return list()


class ProfileFantasy(ProfileStatsPageView):
    template_name = "profiles/fantasy2.html"
    page_title = _('Twoje fantasy')

    def get_data_or_calculate(self, user):
        season_name = get_current_season()
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(fantasy=True) >= 7 and user.profile.has_data_id:
            fantasy = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name, full=True)
            user.profile.playermetrics.update_fantasy(fantasy)
        return user.profile.playermetrics.fantasy


class ProfileCarrierRows(ProfileStatsPageView):
    template_name = 'profiles/carrier_rows.html'
    page_title = _('Twoja kariera')

    def get_data_or_calculate(self, user):
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(games=True) >= 7 and user.profile.has_data_id:
            season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
            user.profile.playermetrics.update_season(season)
        user.profile.playermetrics.refresh_from_db()
        if user.profile.playermetrics.season is None:
            return []
        return user.profile.playermetrics.season


class ProfileCarrier(ProfileStatsPageView, mixins.PaginateMixin):
    """
    coach.data:

    {"2020/2021": {
        "games": [{"date": "2020-11-21", "result": {"name": "P", "type...
        "carrier": {"wons": 2, "draws": 0, "loses": 5, "points": 6, "avg_points": 0.9, "gain_goals": 14, 
            "lost_goals": 11, "games_played": 7, "wons_percent": 28.571428571428573, "draws_percent": 0.0, 
            "loses_percent": 71.42857142857143, "avg_goals_gain": 1.6, "avg_goals_losts": 2.0,
            "position_in_table": 0}
    """
    template_name = "profiles/carrier.html"
    paginate_limit = 16
    page_title = _('Twoja kariera')

    def get_data_or_calculate(self, user):
        data = []
        if user.is_player:
            _id = user.profile.data_mapper_id
            if user.profile.playermetrics.how_old_days(season=True) >= 7 and user.profile.has_data_id:
                season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
                user.profile.playermetrics.update_season(season)
            user.profile.playermetrics.refresh_from_db()
            data = user.profile.playermetrics.season
            if data is None:
                data = []
            data = self.flattern_carrier_structure(data)
            data = self.sort(data)

        elif user.is_coach:
            data = user.profile.get_data() or []
            data = self.flattern_coach_carrier_structure(data)
            data = self.sort(data)
           

        return self.paginate(data)

    def sort(self, data):
        return sorted(data, key=lambda k: k['name'], reverse=True)

    def flattern_coach_carrier_structure(self, data: dict) -> list:
        out = []
        for season, season_data in data.items():
            season_dict = {}
            for team, team_stat in season_data["carrier"]["teams"].items():
                season_dict["name"] = season
                season_dict["team"] = team
                season_dict.update(team_stat)
                out.append(season_dict)
        return out

    def flattern_carrier_structure(self, data: dict) -> list:
        '''
        @todo: this should be in serializers/ package

        season: {'2014/2015':
            {'4 liga':
                {'włókniarz mirsk': {
                    'red_cards': 1,
                    'team_goals': 1,
                    'games_played': 24, 'yellow_cards': 5, 'minutes_played': 1296, 'first_squad_games_played': 17}}}, '2015/2016': {'4 l
        [{season: '2014', leagues: [

        ]}]
        '''
        out = list()
        if not data:
            return out
        for season_name, league_data in data.items():
            for league_name, team_data in league_data.items():
                if not team_data:
                    return out
                for team_name, data in team_data.items():
                    if not data:
                        return out
                    out.append(
                        {
                            'name': season_name,
                            'league': league_name,
                            'team': team_name,
                            'red_cards': data.get('red_cards'),
                            'yellow_cards': data.get('yellow_cards'),
                            'minutes_played': data.get('minutes_played'),
                            'team_goals': data.get('team_goals'),
                            'lost_goals': data.get('lost_goals'),
                            'games_played': data.get('games_played'),
                            'first_squad_games_played': data.get('first_squad_games_played'),
                        }
                    )
        return out


class ProfileGames(ProfileStatsPageView, mixins.PaginateMixin):
    template_name = "profiles/games.html"
    paginate_limit = 15
    page_title = _('Twoje mecze')

    def get_data_or_calculate(self, user):
        if user.is_player:
            _id = user.profile.data_mapper_id
            if user.profile.playermetrics.how_old_days(games=True) >= 7 and user.profile.has_data_id:
                games = adapters.PlayerLastGamesAdapter(_id).get()
                user.profile.playermetrics.update_games(games)
            # user.profile.playermetrics.refresh_from_db()
            data = user.profile.playermetrics.games
            if data is None:
                data = []
            return self.paginate(data)
        elif user.is_coach:
            games_data = user.profile.get_season_games_data(self.season_name)
            if games_data:
                data = games_data
            else:
                data = []
            return self.paginate(data)
