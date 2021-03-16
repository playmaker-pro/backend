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
            return list(map(int, ls))
        else:
            return []

    def get_senior_leagues(self):
        if not self.senior_leagues:
            return []
        ls = self.senior_leagues.split(',')
        if ls:
            return list(map(int, ls))
        else:
            return []

    def get_junior_leagues(self):
        if not self.junior_leagues:
            return []
        ls = self.junior_leagues.split(',')
        if ls:
            return list(map(int, ls))
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
        fantasy.calculate_fantasy_for_player(self.player.profile, self.season.name, self.senior)


class CalculateFantasyStats:
    JUNIOR_LEAGUES = [8, 9, 10, 11, 12, 13]
    SENIOR_LEAGUES = [1, 2, 3, 4, 5, 6, 7, 20, 21, 5000, 5002, 23, 24]
    EXCLUDED_LEAGUES = [14, 15, 16, 17, 18, 19, 100, 5003, 5004, 5005, 5006, 5007, 5023]

    def __init__(self):
        fsetts = FantasySettings.objects.all().first()
        self.junior_leagues = fsetts.get_junior_leagues() or self.JUNIOR_LEAGUES
        self.senior_leagues = fsetts.get_senior_leagues() or self.SENIOR_LEAGUES
        self.excluded_leagues = fsetts.get_excluded_leagues() or self.EXCLUDED_LEAGUES

    def calculate_fantasy_for_player(self, user_profile, season: str, is_senior: bool = True):
        '''need to be player'''
        player = PlayerAdapter(user_profile.data_mapper_id).get_player_object()
        points = 0
        ps = player.playerstats.select_related('game', 'gamefication', 'league', 'season').filter(season__name=season)
        ps = self._filter_players_stats(ps, is_senior=is_senior)
        games_count = ps.count()

        if games_count != 0:
            points = ps.aggregate(Sum('gamefication__score')).get('gamefication__score__sum') or 0
            self.create_or_update_fantasy_object(season, points, games_count, user_profile.user, is_senior)
            user_profile.add_event_log_message(f'Fantasy calculated sucesfully and got {points} points for {season} for senior={is_senior}')
        else:
            self.try_to_remove_fantasy_object(season, user_profile.user, is_senior)
            user_profile.add_event_log_message(f'Player got 0 points for {season} for senior={is_senior}')
            return

    def try_to_remove_fantasy_object(self, season, user, is_senior):
        ss = SeasonService()
        season_object = ss.get(season)
        try:
            pfr = PlayerFantasyRank.objects.get(
                season=season_object,
                player=user,
                senior=is_senior
            )
            pfr.delete()
        except PlayerFantasyRank.DoesNotExist:
            return

    def create_or_update_fantasy_object(self, season: str, points: int, games_count: int, user: User, is_senior):
        ss = SeasonService()
        season_object = ss.get(season)
        PlayerFantasyRank.objects.update_or_create(
            season=season_object,
            player=user,
            senior=is_senior,
            defaults={
                'games_played': games_count,
                'score': points}
            )

    def _filter_players_stats(self, queryset, is_senior=True):
        ll = self.senior_leagues if is_senior else self.junior_leagues
        queryset = queryset.exclude(league__code__in=self.excluded_leagues)
        if ll:
            queryset = queryset.filter(league__code__in=ll)
        return queryset
