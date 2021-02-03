
from django.contrib.auth.mixins import LoginRequiredMixin


from django.utils.translation import gettext_lazy as _
from django.views import generic

from stats import adapters

from .base import SlugyViewMixin

from django.contrib.auth import get_user_model
from utils import get_current_season
from app import mixins
import logging 

User = get_user_model()


logger = logging.getLogger(__name__)


class ProfileStatsPageView(generic.TemplateView, SlugyViewMixin,  mixins.ViewModalLoadingMixin):
    page_title = None
    template_name = None
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = self.select_user_to_show()
        season_name = get_current_season()

        if self._is_owner(user):
            kwargs["editable"] = True
        kwargs['season_name'] = season_name
        kwargs['show_user'] = user
        kwargs['page_obj'] = self.get_data_or_calculate(user)
        kwargs['page_title'] = self.page_title
        kwargs['modals'] = self.modal_activity(request.user)
        return super().get(request, *args, **kwargs)

    def get_data_or_calculate(self, *args, **kwargs):
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
        if user.profile.playermetrics.how_old_days(season=True) >= 7 and user.profile.has_data_id:
            season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
            user.profile.playermetrics.update_season(season)
        user.profile.playermetrics.refresh_from_db()
        if user.profile.playermetrics.season is None:
            return []
        return user.profile.playermetrics.season


class ProfileCarrier(ProfileStatsPageView, mixins.PaginateMixin):
    template_name = "profiles/carrier.html"
    paginate_limit = 16
    page_title = _('Twoja kariera')

    def get_data_or_calculate(self, user):
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
        return self.paginate(data)

    def sort(self, data):
        return sorted(data, key=lambda k: k['name'], reverse=True)

    def flattern_carrier_structure(self, data: dict) -> list:
        '''
        @todo: this shoudl be in serializers/
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
        _id = user.profile.data_mapper_id
        if user.profile.playermetrics.how_old_days(games=True) >= 7 and user.profile.has_data_id:
            games = adapters.PlayerLastGamesAdapter(_id).get()
            user.profile.playermetrics.update_games(games)
        # user.profile.playermetrics.refresh_from_db()
        data = user.profile.playermetrics.games
        if data is None:
            data = []
        return self.paginate(data)
