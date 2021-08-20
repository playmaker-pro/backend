import logging
from collections import defaultdict
from datetime import datetime

import easy_thumbnails
from clubs.models import League as CLeague
from clubs.models import Team as CTeam
from data.models import Game, League, Team, TeamStat
from django.db.models import Avg, Count, Min, Q, Sum
from django.urls import reverse
from easy_thumbnails.files import get_thumbnailer
from rest_framework.serializers import ModelSerializer

logger = logging.getLogger(__name__)


class TeamStatSerializer:
    @classmethod
    def calc(cls, teamstat):
        return {
            "result": teamstat.result,
            "side": teamstat.side,
            "points": teamstat.points,
            "lost_goals": teamstat.lost_goals,
            "gain_goals": teamstat.gain_goals,
            # "game": teamstat.game.date,
            # "league_code": teamstat.game.league.code,
            # "league_name": teamstat.game.league.name,
        }


class LeagueMatches:
    def serialize(self):
        pass


class TeamMetrics:
    def serialize(self, team_name, season_name, league_code):
        total = TeamStat.objects.filter(
            team__name=team_name,
            game__season__name=season_name,
            game__league__code=league_code,
        ).order_by("-game__date")

        points = total.aggregate(Sum("points"))
        gain_goals = total.aggregate(Sum("gain_goals"))
        lost_goals = total.aggregate(Sum("lost_goals"))
        wons = total.filter(result=1)

        losts = total.filter(result=2)
        total_count = total.count()
        wons_count = wons.count()
        losts_count = losts.count()
        trend = total[:5]
        """{
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
        """
        trends = []
        for t in trend:
            if t.result == 1:
                trd = "W"
            elif t.result == 2:
                trd = "P"
            elif t.result == 0:
                trd = "R"
            trends.append(trd)
        output = {
            "team": team_name,
            "games": total_count,
            "wins": wons_count,
            "losts": losts_count,
            "draws": total_count - wons_count - losts_count,
            "points": points["points__sum"],
            "goals": f"{gain_goals['gain_goals__sum']}:{lost_goals['lost_goals__sum']}",
            "trend": trends,
        }

        return output


class TeamMapper:
    @classmethod
    def get_team_obj(cls, team_name, league_obj):
        from clubs.models import Team as CTeam

        try:
            team_obj = CTeam.objects.get(
                league=league_obj, mapping__icontains=team_name.lower()
            )
            return team_obj
        except CTeam.DoesNotExist:
            return None

    @classmethod
    def get_url_pic_name(cls, team_name: str, league_obj: CLeague):
        """Returns tuple of (Url, Picture Url, name)"""
        obj = TeamMapper.get_team_obj(team_name, league_obj)
        name = obj.name if obj else team_name
        url = obj.get_permalink() if obj else None
        picture = obj.picture if obj else "default_profile.png"
        try:
            pic = get_thumbnailer(picture)["nav_avatar"].url
        except easy_thumbnails.exceptions.InvalidImageFormatError as e:
            print(picture)
            logger.exception(e)
            raise e

        return url, pic, name


class GameSerializer:
    """
    host_team =
    guest_team =
    host_score = models.IntegerField(null=True)
    host_coach = models.ForeignKe
    host_team_name = models.TextField()
    guest_score = models.IntegerField(null=True)
    guest_coach = models.Foreign
    guest_team_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
            {"name": "Kolejka 30",
                "games": [
                    {
                        "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                        "host": "Sokół I",
                        "guest": "Lechia Dzierżoniów",
                        "score": "2 - 1",
                        "date": "10.05 21:00",
    """

    @classmethod
    def calc(cls, game, host_pic, guest_pic, league):
        # thumbnailer = get_thumbnailer('animals/aardvark.jpg')

        # thumbnail_options = {'crop': True}
        # for size in (50, 100, 250):
        #     thumbnail_options.update({'size': (size, size)})
        #     thumbnailer.get_thumbnail(thumbnail_options)

        # # or to get a thumbnail by alias
        # thumbnailer['large']
        # try:
        #     host_pic = get_thumbnailer(host_picture)['nav_avatar']
        # except:
        #     host_pic = ''
        # try:
        #     guest_pic = get_thumbnailer(guest_picture)['nav_avatar']
        # except:
        #     guest_pic = ''
        league_obj = league

        guest_pic = ""
        host_pic = ""
        host_obj = TeamMapper.get_team_obj(
            game.host_team_name, league_obj
        )  # @todo: rafal
        host_name = host_obj.name if host_obj else game.host_team_name
        host_url = host_obj.get_permalink() if host_obj else None
        if host_obj:
            if host_obj.picture:
                host_pic = get_thumbnailer(host_obj.picture)["nav_avatar"].url

        guest_obj = TeamMapper.get_team_obj(game.guest_team_name, league_obj)
        guest_name = guest_obj.name if guest_obj else game.guest_team_name
        guest_url = guest_obj.get_permalink() if guest_obj else None
        # picture = obj.picture if obj else 'default_profile.png'
        #
        if guest_obj:
            if guest_obj.picture:
                guest_pic = get_thumbnailer(guest_obj.picture)["nav_avatar"].url

        return {
            "guest_pic": guest_pic,
            "host_pic": host_pic,
            "date": game.date.strftime("%Y/%d/%m, %H:%M"),
            "score": f"{game.host_score} - {game.guest_score}",
            "host_url": host_url,
            "host": host_name,
            "guest": guest_name,
            "guest_url": guest_url,
            "url": game.league._url,
        }


class LeagueChildrenSerializer:
    def serialize(self, league):
        output = []
        for leg in league.league_set.all():

            output.append(
                {
                    "url": reverse("plays:summary", kwargs={"slug": leg.slug}),
                    "name": leg.name,
                }
            )
        return output


class SummarySerializer:
    @classmethod
    def serialize(cls, league, season_name):
        output = {}
        output["today_games"] = []
        output["next_games"] = []
        output["current_games"] = []

        try:
            data_index = league.historical.all().get(season__name=season_name)
        except:
            return []

        today_matches = (
            Game.objects.select_related("league", "season")
            .filter(
                league___url=League.get_url_based_on_id(data_index.index),
                season__name=season_name,
                date=datetime.today(),
            )
            .order_by("date")
        )

        next_games = (
            Game.objects.select_related("league", "season")
            .filter(
                league___url=League.get_url_based_on_id(data_index.index),
                season__name=season_name,
                host_score__isnull=True,
                guest_score__isnull=True,
            )
            .order_by("date")[:12]
        )

        current_games = (
            Game.objects.select_related("league", "season")
            .filter(
                league___url=League.get_url_based_on_id(data_index.index),
                season__name=season_name,
                host_score__isnull=False,
                guest_score__isnull=False,
            )
            .order_by("-date")[:12]
        )

        host_pic = ""
        guest_pic = ""

        current_games_output = defaultdict(list)

        for c_game in current_games:
            q = c_game.queue
            current_games_output[q].append(
                GameSerializer.calc(c_game, host_pic, guest_pic, league)
            )
        output["current_games"] = current_games_output

        next_games_output = defaultdict(list)
        for n_game in next_games:
            q = n_game.queue
            next_games_output[q].append(
                GameSerializer.calc(n_game, host_pic, guest_pic, league)
            )
        output["next_games"] = next_games_output

        today_output = defaultdict(list)
        for t_game in today_matches:
            q = t_game.queue
            today_output[q].append(
                GameSerializer.calc(t_game, host_pic, guest_pic, league)
            )
        output["today_games"] = today_output

        return dict(output)


class LeagueMatchesMetrics:
    def serialize(self, league, season_name, played=True, sort_up=True):
        if sort_up:
            date_sort = "-date"
        else:
            date_sort = "date"
        try:
            data_index = league.historical.all().get(season__name=season_name)
        except:
            return []

        # @todo: add date check
        if (
            data_index.data is not None
            and "matches_played" in data_index.data
            and played
        ):
            return data_index.data["matches_played"]

        elif (
            data_index.data is not None and "matches" in data_index.data and not played
        ):
            return data_index.data["matches"]

        if played:
            matches = (
                Game.objects.select_related("league", "season")
                .filter(
                    league___url=League.get_url_based_on_id(data_index.index),
                    season__name=season_name,
                    host_score__isnull=False,
                    guest_score__isnull=False,
                )
                .order_by(date_sort)
            )
        else:
            matches = (
                Game.objects.select_related("league", "season")
                .filter(
                    league___url=League.get_url_based_on_id(data_index.index),
                    season__name=season_name,
                    host_score__isnull=True,
                    guest_score__isnull=True,
                )
                .order_by(date_sort)
            )

        output = defaultdict(list)
        for game in matches:
            q = game.queue
            # try:
            #     host_pic = CTeam.objects.get(name__icontains=game.host_team_name)
            # except:
            #     host_pic = ''
            # try:
            #     guest_pic = CTeam.objects.get(name__icontains=game.guest_team_name)
            # except:
            #     guest_pic = ''
            guest_pic = "default_profile.png"
            host_pic = "default_profile.png"
            output[q].append(GameSerializer.calc(game, host_pic, guest_pic, league))
        if data_index.data is None:
            data_index.data = {}

        if played:
            data_index.data["matches_played"] = dict(output)
        else:
            data_index.data["matches"] = dict(output)
        data_index.save()
        return output


class GameRawSerializer:
    """
    {'date': '23/07/2021 18:00',
     'host': 'BRUK-BET Termalica Nieciecza',
     'guest': 'FKS Stal Mielec S. A.',
     'place': 'Stadion Sportowy BRUK-BET TERMALICA Nieciecza (Nieciecza 150)',
     'queue': '1 kolejka',
     'score': '1:1',
     'league': 'Ekstraklasa "PKO Bank Polski Ekstraklasa"',
     '_url_host': 'https://www2.laczynaspilka.pl/druzyna/bruk-bet-termalica-nieciecza,434083.html',
     '_url_guest': 'https://www2.laczynaspilka.pl/druzyna/fks-stal-mielec-s-a,450461.html',
     'game_action': 'relacja z meczu ›',
     '_url_game_relation': 'https://www2.laczynaspilka.pl/rozgrywki/mecz/bruk-bet-termalica-nieciecza,fks-stal-mielec-s-a,2980870.html'
    }
    """

    def serialize(self, obj, host_pic, guest_pic):
        obj["host_pic"] = host_pic
        obj["guest_pic"] = guest_pic
        return obj


class LeagueAdvancedTableRawMetrics:
    """
    [{      "position": "1",
            "icon": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
            "team": "Manchaster",
            "games": 23,
            "wins": 2,
            "losts": 21,
            "draws": 0,
            "goals": "23:44",
            "points": 42,
            "trend": ["W", "L", "W", "W", "P", "P", "R"],},]
    {'results':
        {'points': '25', 'matches': '30', 'wins_all': '6', 'draws_all': '7',
         'goals_all': '29:60', 'loses_all': '17', 'wins_away': '0', 'wins_home': '6',
         'draws_away': '3', 'draws_home': '4', 'goals_away': '12:23',
         'goals_home': '17:23', 'loses_away': '12', 'loses_home': '5', 'wins_direct': '0', 'draws_direct
    """

    @classmethod
    def serialize(cls, lg, data_index):
        url = League.get_url_based_on_id(data_index.index)
        league = League.objects.get(_url=url)
        # because league with ID == League within Season
        output = []
        for pos, row in enumerate(league.advanced_json, 1):
            last_games = (
                Game.objects.select_related("league")
                .filter(
                    (
                        Q(host_team_name=row.get("club_name"))
                        | Q(guest_team_name=row.get("club_name"))
                    )
                    & Q(league=league)
                    & Q(host_score__isnull=False)
                    & Q(guest_score__isnull=False)
                )
                .order_by("date")[:5]
            )
            league_obj = lg
            team_url, team_pic, team_name = TeamMapper.get_url_pic_name(
                row.get("club_name"), league_obj
            )
            # raise RuntimeError(row.get('club_name'), team_name)
            data = {
                "position": pos,
                "games": row["results"].get("matches"),
                "pic": team_pic,
                "team": team_name,
                "team_url": team_url,
                "losts": row["results"].get("loses_all"),
                "wins": row["results"].get("wins_all"),
                "draws": row["results"].get("draws_all"),
                "goals": row["results"].get("goals_all"),
                "points": row["results"].get("points"),
                "trend": [
                    TrendSerializer.serialize(i, row.get("club_name"))
                    for i in last_games
                ],
            }
            output.append(data)
        return output


class TrendSerializer:
    @classmethod
    def serialize(cls, game, team_name):
        return game.is_winning_team(team_name)


class LeagueMatchesRawMetrics:
    serializer = GameRawSerializer()

    def serialize(self, league, season_name):

        url = League.get_url_based_on_id(league.index)
        league = League.objects.get(_url=url)

        output = defaultdict(list)

        for game in league.games_snapshot:
            q = game.queue
            # try:
            #     host_pic = CTeam.objects.get(name__icontains=game.host_team_name)
            # except:
            #     host_pic = ''
            # try:
            #     guest_pic = CTeam.objects.get(name__icontains=game.guest_team_name)

            # except:
            host_pic = ""
            guest_pic = ""
            output[q].append(self.serializer.serialize(game, host_pic, guest_pic))
        return output


from .serializers import CoachProfileSerializer, PlayerProfileSerializer


class PlaymakerMetrics:
    @classmethod
    def calc(cls, league):
        from profiles.models import CoachProfile, PlayerProfile

        players = PlayerProfile.objects.filter(team_object__league=league)
        coaches = CoachProfile.objects.filter(team_object__league=league)
        data = {}

        data["coaches"] = CoachProfileSerializer.serialize(coaches)
        data["players"] = PlayerProfileSerializer.serialize(players)
        return data
