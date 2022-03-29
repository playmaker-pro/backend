import logging
from collections import defaultdict
from datetime import datetime

from .serializers import CoachProfileSerializer, PlayerProfileSerializer, SimplePlayerProfileSerializer, GameSerializer, GameRawSerializer, TrendSerializer
from django.contrib.postgres.aggregates import ArrayAgg
from data.models import Game as DGame
from clubs.models import League as CLeague
from clubs.models import LeagueHistory as CLeagueHistory
from data.models import Game, League, Team, TeamStat
from django.db.models import Avg, Count, Min, Q, Sum
from django.urls import reverse
from .mappers import TeamMapper, PlayerMapper
from profiles.models import CoachProfile, PlayerProfile


logger = logging.getLogger(__name__)


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
        _number_of_last_games = 12
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
            .annotate(players_ids=ArrayAgg('playerstat__player'))
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
            .annotate(players_ids=ArrayAgg('playerstat__player'))
            .order_by("date")[:_number_of_last_games]
        )

        current_games = (
            Game.objects.select_related("league", "season")
            .filter(
                league___url=League.get_url_based_on_id(data_index.index),
                season__name=season_name,
                host_score__isnull=False,
                guest_score__isnull=False,
            )
            .annotate(players_ids=ArrayAgg('playerstat__player'))
            .order_by("-date")[:_number_of_last_games]
        )

        host_pic = ""
        guest_pic = ""

        current_games_output = dict()

        for c_game in current_games:
            q = c_game.queue
            if not current_games_output.get(q):
                current_games_output[q] = []

            current_games_output[q].append(
                GameSerializer.serialize(c_game, host_pic, guest_pic, league)
            )
        output["current_games"] = current_games_output

        next_games_output = dict()
        for n_game in next_games:
            q = n_game.queue
            if not next_games_output.get(q):
                next_games_output[q] = []
            next_games_output[q].append(
                GameSerializer.serialize(n_game, host_pic, guest_pic, league)
            )
        output["next_games"] = next_games_output

        today_output = dict()
        for t_game in today_matches:
            q = t_game.queue
            if not today_output.get(q):
                today_output[q] = []
            today_output[q].append(
                GameSerializer.serialize(t_game, host_pic, guest_pic, league)
            )
        output["today_games"] = today_output

        return dict(output)


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
        if league.advanced_json is None:
            return output
        # TypeError: 'NoneType' object is not iterable
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
            tm = TeamMapper()

            team_url, team_pic, team_name = tm.get_url_pic_name(
                row.get("club_name"), league_obj
            )

            tm.team_object.get_club_pic()

            club_pic = tm.team_object.get_club_pic()

            # raise RuntimeError(row.get('club_name'), team_name)
            data = {
                "position": pos,
                "games": row["results"].get("matches"),
                "pic": team_pic,
                "team": team_name,
                "team_url": team_url,
                "team_pic": club_pic,
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


class PlaymakerMetrics:
    @classmethod
    def calc(cls, league):
        players = PlayerProfile.objects.filter(team_object__league=league)
        coaches = CoachProfile.objects.filter(team_object__league=league)
        data = {}

        data["coaches"] = CoachProfileSerializer.serialize(coaches)
        data["players"] = PlayerProfileSerializer.serialize(players)
        return data
