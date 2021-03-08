from django.db import models
from clubs.models import Season, Seniority
from clubs.services import SeasonService

from utils import get_current_season
from django.contrib.auth import get_user_model
from stats.adapters.player import PlayerAdapter
from django.db.models import Sum

User = get_user_model()


class FantasySettings(models.Model):
    excluded_leagues = models.TextField(help_text='Comma separated numbers eg. "20,21,23" ', null=True, blank=True)
    senior_leagues = models.TextField(help_text='Comma separated numbers eg. "20,21,23" ', null=True, blank=True)
    junior_leagues = models.TextField(help_text='Comma separated numbers eg. "20,21,23" ', null=True, blank=True)

    def get_excluded_leagues(self):
        if not self.excluded_leagues:
            return []
        ls = self.excluded_leagues.split(',')

        if ls:
            return ls
        else:
            return []

    def get_senior_leagues(self):
        if not self.senior_leagues:
            return []
        ls = self.senior_leagues.split(',')
        if ls:
            return ls
        else:
            return []

    def get_junior_leagues(self):
        if not self.junior_leagues:
            return []
        ls = self.junior_leagues.split(',')
        if ls:
            return ls
        else:
            return []


class PlayerFantasyRank(models.Model):
    updated = models.DateTimeField(auto_created=True, auto_now=True)
    season = models.ForeignKey(Season, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    player = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    score = models.IntegerField(default=0, db_index=True)
    games_played = models.IntegerField(default=None, null=True, blank=True)
    senior = models.BooleanField(default=False)

    class Meta:
        unique_together = ('player', 'season', 'senior')

    def __unicode__(self):
        return f'{self.player}:{self.season}'

    def calculate(self):
        fantasy = CalculateFantasyStats()
        fantasy.calculate_fantasy_for_player(self.player, self.season.name, self.senior)


class CalculateFantasyStats:
    JUNIOR_LEAGUES = [8, 9, 10, 11, 12, 13]
    SENIOR_LEAGUES = [1, 2, 3, 4, 5, 6, 7, 20, 21, 5000, 5002, 23, 24]
    EXCLUDED_LEAGUES = [14, 15, 16, 17, 18, 19, 100, 5003, 5004, 5005, 5006, 5007, 5023]

    def __init__(self):
        fsetts = FantasySettings.objects.all().first()
        self.junior_leagues = fsetts.get_senior_leagues() or self.JUNIOR_LEAGUES
        self.senior_leagues = fsetts.get_senior_leagues() or self.SENIOR_LEAGUES
        self.excluded_leagues = fsetts.get_excluded_leagues() or self.EXCLUDED_LEAGUES

    def calculate_fantasy_for_player(self, user_profile, season: str, senior: bool = True):
        '''need to be player'''
        player = PlayerAdapter(user_profile.data_mapper_id).get_player_object()
        points = 0
        ps = player.playerstats.select_related('game', 'gamefication', 'league', 'season').filter(season__name=season)
        ps = self._filter_players_stats(ps, senior=senior)
        games_count = ps.count()

        if games_count != 0:
            points = ps.aggregate(Sum('gamefication__score')).get('gamefication__score__sum') or 0
            self.create_or_update_fantasy_object(season, points, games_count, user_profile.user, senior)
        else:
            # @todo: here some event log...
            return

    def _filter_leagues(self, queryset, league_filter):
        return queryset.filter(league__code__in=league_filter)

    def _filter_players_stats(self, queryset, senior=True):
        ll = self.senior_leagues if senior else self.junior_leagues
        queryset = self._filter_leagues(queryset, ll)
        queryset = queryset.exclude(league__code__in=self.excluded_leagues)

        # Commented according to CR-8.3
        # if self.query_league:
        #     queryset = queryset.filter(league__code=reverse_translate_league_name(self.query_league))

        # if self.query_team:
        #     queryset = queryset.filter(team_name=reverse_translate_team_name(self.query_team))

        # if self.query_zpn:
        #     queryset = queryset.filter(league__zpn_code_name=self.query_zpn)
        return queryset

    def create_or_update_fantasy_object(self, season: str, points: int, games_count: int, user: User, senior):
        ss = SeasonService()
        season_object = ss.get(season)
        PlayerFantasyRank.objects.update_or_create(
            season=season_object,
            player=user,
            senior=senior,
            defaults={
                'games_played': games_count,
                'score': points}
            )
