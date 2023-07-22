import logging

from django.contrib.postgres.aggregates import ArrayAgg

from clubs.models import League as CLeague
from clubs.models import LeagueHistory as CLeagueHistory

# from data.models import Game, League  DEPRECATED: PM-1015

from .serializers import GameSerializer

logger = logging.getLogger(__name__)


class LeagueMatchesMetrics:
    _default_pic = "default_profile.png"

    def calculate(
        self,
        league: CLeague,
        season_name: str,
        league_history: CLeagueHistory = None,
        played: bool = True,
        sort_up: bool = True,
        overwrite: bool = False,
    ):
        # print(f">> Param passed league: {type(league)}, ({league})")
        # print(f">> Param passed season_name: {type(season_name)}, ({season_name})")
        # print(
        #     f">> Param passed league_history: {type(league_history)}, ({league_history})"
        # )
        # print(f">> Param passed played: {type(played)}, ({played})")
        #
        # if sort_up:
        #     date_sort = "-date"
        # else:
        #     date_sort = "date"
        #
        # league_history = self.get_league_history(league, season_name, league_history)
        # if league_history is None:
        #     return []
        #
        # if played:
        #     keyname = "matches_played"
        #     matches, calculated = self.calculate_matches_played(
        #         league_history, overwrite=overwrite, sort_by=date_sort
        #     )
        # else:
        #     keyname = "matches"
        #     matches, calculated = self.calculate_matches(
        #         league_history, overwrite=overwrite, sort_by=date_sort
        #     )
        # if calculated:
        #     output = dict()  # OrderedDict()
        #     for game in matches:
        #         # q = game.queue  # if we do not do values ealier
        #         q = game["queue"]
        #         guest_pic = self._default_pic
        #         host_pic = self._default_pic
        #         if not output.get(q):
        #             output[q] = list()
        #         output[q].append(
        #             GameSerializer.serialize(
        #                 game, host_pic, guest_pic, league_history.league
        #             )
        #         )
        #
        #     if league_history.data is None:
        #         print("........Data_index is None, making empty one.")
        #         league_history.data = {}
        #
        #     print("........setting matches")
        #     league_history.data[keyname] = output  # OrderedDict(output)
        #     # data_index.data = data
        #
        #     print(
        #         f"........Saving... data_index....{league_history} {type(league_history)}"
        #     )
        #     league_history.save()
        #
        #     return output
        # else:
        #     return matches
        return

    def get_league_history(
        self, league: CLeague, season_name: str, league_history: CLeagueHistory = None
    ):
        # todo: that might not be needed. Due to leagacy implementation we were
        #       using season_name and league object to find LeagueHistory object
        #       right now it is not needed, we can rely only on LH object.

        if league_history is not None:
            return league_history
        else:
            try:
                return league.historical.all().get(season__name=season_name)
            except Exception as e:
                print(f"When getting league history following error occured: {e}")
                return

    def calculate_matches(
        self,
        league_history: CLeagueHistory = None,
        overwrite: bool = False,
        sort_by: str = "date",
    ):
        # keyname = "matches"
        # season_name = league_history.season.name
        # if (
        #     league_history.data is not None
        #     and keyname in league_history.data
        #     and not overwrite
        # ):
        #     print(f"Geting data for matches. overwrite={overwrite}")
        #     return league_history.data["matches"], False
        # else:
        #     print(
        #         f"===> Calculating Game data for {league_history.league} season={season_name}"
        #     )
        #     matches = (
        #         Game.objects.select_related("league", "season")
        #         .filter(
        #             league___url=League.get_url_based_on_id(league_history.index),
        #             season__name=season_name,
        #             host_score__isnull=True,
        #             guest_score__isnull=True,
        #         )
        #         .annotate(players_ids=ArrayAgg("playerstat__player"))
        #         .order_by(sort_by)
        #         .values(
        #             "queue",
        #             "date",
        #             "host_score",
        #             "guest_score",
        #             "host_team_name",
        #             "guest_team_name",
        #             "players_ids",
        #         )
        #     )
        #     return matches, True
        return None, None

    def calculate_matches_played(
        self,
        league_history: CLeagueHistory = None,
        overwrite: bool = False,
        sort_by: str = "date",
    ):
        # keyname = "matches_played"
        # season_name = league_history.season.name
        #
        # if (
        #     league_history.data is not None
        #     and keyname in league_history.data
        #     and not overwrite
        # ):
        #     print(f"Geting data for matches. overwrite={overwrite}")
        #     return league_history.data[keyname], False
        # else:
        #     matches = (
        #         Game.objects.select_related("league", "season")
        #         .filter(
        #             league___url=League.get_url_based_on_id(league_history.index),
        #             season__name=season_name,
        #             host_score__isnull=False,
        #             guest_score__isnull=False,
        #         )
        #         .annotate(players_ids=ArrayAgg("playerstat__player"))
        #         .order_by(sort_by)
        #         .values(
        #             "queue",
        #             "date",
        #             "host_score",
        #             "guest_score",
        #             "host_team_name",
        #             "guest_team_name",
        #             "players_ids",
        #         )
        #     )
        #     return matches, True
        return None, None

    # def serialize(
    #     self,
    #     league: CLeague,
    #     season_name: str,
    #     league_history: CLeagueHistory = None,
    #     played: bool = True,
    #     sort_up: bool = True,
    #     overwrite: bool = False,
    # ):
    #     """
    #     :param overwrite: Overwirte data if present in cache
    #     :param sort_up: defines if decending or ascending

    #     """

    # _default_pic = "default_profile.png"
    # logger.info("League matches metrics calculation started.")
    # if sort_up:
    #     date_sort = "-date"
    # else:
    #     date_sort = "date"

    # if league_history is not None:
    #     data_index = league_history
    # else:
    #     try:
    #         data_index = league.historical.all().get(season__name=season_name)
    #     except Exception as e:
    #         print(f"Error occured {e}")
    #         return []

    # # @todo: add date check
    # if (
    #     data_index.data is not None
    #     and "matches_played" in data_index.data
    #     and played
    #     and not overwrite
    # ):
    #     print(f'Geting data for matched_played. overwrite={overwrite}')
    #     return data_index.data["matches_played"]

    # elif (
    #     data_index.data is not None
    #     and "matches" in data_index.data
    #     and not played
    #     and not overwrite
    # ):
    #     print(f'Geting data for matches. overwrite={overwrite}')
    #     return data_index.data["matches"]
    # else:
    #     print(f'===> Calculating Game data for {league} season={season_name}')
    #     if played:
    #         matches = (
    #             Game.objects.select_related("league", "season")
    #             .filter(
    #                 league___url=League.get_url_based_on_id(data_index.index),
    #                 season__name=season_name,
    #                 host_score__isnull=False,
    #                 guest_score__isnull=False,
    #             )
    #             .annotate(players_ids=ArrayAgg('playerstat__player'))
    #             .order_by(date_sort)
    #             .values(
    #                 "queue",
    #                 "date",
    #                 "host_score",
    #                 "guest_score",
    #                 "host_team_name",
    #                 "guest_team_name",
    #                 "players_ids",
    #             )
    #         )
    #     else:
    #         matches = (
    #             Game.objects.select_related("league", "season")
    #             .filter(
    #                 league___url=League.get_url_based_on_id(data_index.index),
    #                 season__name=season_name,
    #                 host_score__isnull=True,
    #                 guest_score__isnull=True,
    #             )
    #             .annotate(players_ids=ArrayAgg('playerstat__player'))
    #             .order_by(date_sort)
    #             .values(
    #                 "queue",
    #                 "date",
    #                 "host_score",
    #                 "guest_score",
    #                 "host_team_name",
    #                 "guest_team_name",
    #                 "players_ids",
    #             )
    #         )

    #     output = dict()  # OrderedDict()
    #     for game in matches:
    #         # q = game.queue  # if we do not do values ealier
    #         q = game["queue"]
    #         guest_pic = _default_pic
    #         host_pic = _default_pic
    #         if not output.get(q):
    #             output[q] = list()
    #         output[q].append(GameSerializer.serialize(game, host_pic, guest_pic, league))

    #     if data_index.data is None:
    #         print(">> Data_index is None, making empty one.")
    #         data_index.data = {}

    #     if played:
    #         # data_index.data["matches_played"] = {}
    #         print('...........setting matches_played')
    #         # data = data_index.data.copy()
    #         data_index.data["matches_played"] = output  # OrderedDict(output)
    #         # print(data_index.data["matches_played"])
    #         #data_index.data = data

    #     else:
    #         # data_index.data["matches"] = {}
    #         print('...........setting matches')
    #         #data = data_index.data.copy()
    #         data_index.data["matches"] = output  # OrderedDict(output)
    #         #data_index.data = data

    #     print(f'Saving... data_index....{data_index} {type(data_index)}')
    #     data_index.save()

    # return output
