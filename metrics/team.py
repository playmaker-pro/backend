import logging
from collections import defaultdict
from datetime import datetime
from data.models import Game as DGame
import easy_thumbnails
from clubs.models import League as CLeague
from clubs.models import LeagueHistory as CLeagueHistory
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
        picture = obj.picture if obj and obj.picture else "default_profile.png"
        try:
            pic = get_thumbnailer(picture)["nav_avatar"].url
        except easy_thumbnails.exceptions.InvalidImageFormatError as e:
            logger.error(f"Picture is: `{picture}`")
            logger.exception(picture)
            if obj.picture:
                raise RuntimeError(
                    f"picture={picture}, obj={obj} obj.picture={obj.picture}"
                )
            else:
                raise RuntimeError(f"picture={picture}, obj={obj}")

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

    : Return :

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
    def calc(cls, game, host_pic, guest_pic, league: CLeague):
        if isinstance(game, DGame):
            return cls.calculate_from_obj(game, host_pic, guest_pic, league)
        elif isinstance(game, dict):
            return cls.calculate_from_dict(game, host_pic, guest_pic, league)
        else:
            raise RuntimeError("Wrong type of data to process.")

    @classmethod
    def calculate_from_obj(cls, game, host_pic, guest_pic, league: CLeague):
        h_url, h_pic, h_name = TeamMapper.get_url_pic_name(game.host_team_name, league)
        g_url, g_pic, g_name = TeamMapper.get_url_pic_name(game.guest_team_name, league)
        score = (
            f"{game.host_score} - {game.guest_score}"
            if game.host_score and game.guest_score
            else None
        )
        return {
            "guest_pic": g_pic,
            "host_pic": h_pic,
            "date": cls.clean_date(game.date),
            "score": score,
            "host_url": h_url,
            "host": h_name,
            "guest": g_name,
            "guest_url": g_url,
            "guest_score": game.host_score,
            "host_score": game.guest_score,
            # "url": game.league._url,
        }

    @classmethod
    def add_timezone_to_datetime(cls, date: datetime) -> datetime:
        """Two systems uses different date nottation. +2h is needed to shift"""
        from datetime import timedelta

        return date + timedelta(hours=2)

    @classmethod
    def convert_datetime_to_string(cls, date: datetime) -> str:
        return date.strftime("%Y/%d/%m, %H:%M")

    @classmethod
    def clean_date(cls, date: datetime) -> str:
        date = cls.add_timezone_to_datetime(date)
        return cls.convert_datetime_to_string(date)

    @classmethod
    def calculate_from_dict(cls, game, host_pic, guest_pic, league: CLeague):
        h_url, h_pic, h_name = TeamMapper.get_url_pic_name(
            game["host_team_name"], league
        )
        g_url, g_pic, g_name = TeamMapper.get_url_pic_name(
            game["guest_team_name"], league
        )
        score = (
            f"{game['host_score']} - {game['guest_score']}"
            if game["host_score"] and game["guest_score"]
            else None
        )
        return {
            "guest_pic": g_pic,
            "host_pic": h_pic,
            "date": cls.clean_date(game["date"]),
            "score": score,
            "host_url": h_url,
            "host": h_name,
            "guest": g_name,
            "guest_url": g_url,
            "guest_score": game["host_score"],
            "host_score": game["guest_score"],
            # "url": game.league._url,
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
                GameSerializer.calc(c_game, host_pic, guest_pic, league)
            )
        output["current_games"] = current_games_output

        next_games_output = dict()
        for n_game in next_games:
            q = n_game.queue
            if not next_games_output.get(q):
                next_games_output[q] = []
            next_games_output[q].append(
                GameSerializer.calc(n_game, host_pic, guest_pic, league)
            )
        output["next_games"] = next_games_output

        today_output = dict()
        for t_game in today_matches:
            q = t_game.queue
            if not today_output.get(q):
                today_output[q] = []
            today_output[q].append(
                GameSerializer.calc(t_game, host_pic, guest_pic, league)
            )
        output["today_games"] = today_output

        return dict(output)


class LeagueMatchesMetrics:
    def serialize(
        self,
        league: CLeague,
        season_name: str,
        league_history: CLeagueHistory = None,
        played: bool = True,
        sort_up: bool = True,
        overwrite: bool = False,
    ):
        """
        :param overwrite: Overwirte data if present in cache
        :param sort_up: defines if decending or ascending

        """
        _default_pic = "default_profile.png"
        logger.info("League matches metrics calculation started.")
        if sort_up:
            date_sort = "-date"
        else:
            date_sort = "date"

        if league_history is not None:
            data_index = league_history
        else:
            try:
                data_index = league.historical.all().get(season__name=season_name)
            except:
                return []

        # @todo: add date check

        if (
            data_index.data is not None
            and "matches_played" in data_index.data
            and played
            and not overwrite
        ):
            print(f'Geting data for matched_played. overwrite={overwrite}')
            return data_index.data["matches_played"]

        elif (
            data_index.data is not None
            and "matches" in data_index.data
            and not played
            and not overwrite
        ):
            print(f'Geting data for matches. overwrite={overwrite}')
            return data_index.data["matches"]
        print(f'===> Calculating Game data for {league} season={season_name}')
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
                .values(
                    "queue",
                    "date",
                    "host_score",
                    "guest_score",
                    "host_team_name",
                    "guest_team_name",
                )
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
                .values(
                    "queue",
                    "date",
                    "host_score",
                    "guest_score",
                    "host_team_name",
                    "guest_team_name",
                )
            )
        from collections import OrderedDict

        output = OrderedDict()
        for game in matches:
            # q = game.queue  # if we do not do values ealier
            q = game["queue"]
            guest_pic = _default_pic
            host_pic = _default_pic
            if not output.get(q):
                output[q] = list()
            output[q].append(GameSerializer.calc(game, host_pic, guest_pic, league))

        if data_index.data is None:
            data_index.data = {}

        if played:
            data_index.data["matches_played"] = {}
            print('...........setting matches_played')
            data_index.data["matches_played"] = OrderedDict(output)
            print(data_index.data["matches_played"])
        else:
            data_index.data["matches"] = {}
            print('...........setting matches')
            data_index.data["matches"] = OrderedDict(output)
        print('Saving... data_index....')
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
