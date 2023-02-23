import typing
from abc import abstractmethod
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from pm_core.services.models import (
    GameSchema,
    EventSchema,
    PlayerSeasonStatsSchema,
    PlayerSeasonStatsListSchema,
    GamesSchema,
)
from adapters.exceptions import (
    WrongDataFormatException,
    DataShortageLogger,
)
from adapters.utils import resolve_stats_list
from itertools import groupby
from mapper.models import MapperEntity


class BasePlayerSerializer:
    @property
    @abstractmethod
    def data(self) -> typing.Dict:
        """data property abstract method"""
        ...

    def resolve_team_name(self, team_id: str) -> typing.Union[str, None]:
        """get team name from s51"""
        try:
            team_entity = MapperEntity.objects.get(mapper_id=team_id)
        except ObjectDoesNotExist:  # maybe display name from api in case?
            return

        return team_entity.target.teamhistory.team.name

    def get_league_name(self, _id: str) -> str:
        """get league name from s51 (scrapper has different league names)"""
        entity = MapperEntity.objects.filter(mapper_id=_id).first()
        if entity:
            return entity.target.leaguehistory.league.highest_parent.name


class GameSerializer(BasePlayerSerializer):
    def __init__(self, data: GamesSchema, limit: int = None) -> None:
        """
        data - array of games
        limit - determine how many games do you want to get (sort desc by date)
        """
        if data and not isinstance(data[0], GameSchema):
            raise WrongDataFormatException(self, GameSchema, type(data[0]))

        self.games: GamesSchema = data
        self.limit: int = limit

    def resolve_cards(self, cards: typing.List[EventSchema]) -> typing.Tuple[int, int]:
        """get count of cards from game"""
        _yellow, _red = 0, 0
        for card in cards:
            if card.type == "Yellow":
                _yellow += 1
            elif card.type == "Red":
                _red += 1
        return _yellow, _red

    def format_date(self, date: str, pattern: str) -> str:
        """format date of game based on given pattern"""
        date = datetime.strptime(date, "%m/%d/%Y %H:%M:%S")
        return date.strftime(pattern)

    @property
    def data(self) -> typing.List:
        """get serialized list of games (desc sort)"""
        if self.limit:
            return self.parse_games()[: self.limit]
        return self.parse_games()

    def parse_games(self) -> typing.List:
        """translate new games data like old serializer"""
        games = []

        for game in self.games.__root__:
            final_result = game.scores.final
            player_team = (
                game.host if game.player_current_team == game.host.id else game.guest
            )
            enemy_team = game.guest if player_team is game.host else game.host
            host_score, guest_score = final_result.split(":")

            team_goals = {
                game.host.name: host_score,
                game.guest.name: guest_score,
            }

            parsed_game = {
                "host_team_name": self.resolve_team_name(game.host.id)
                or game.host.name,
                "guest_team_name": self.resolve_team_name(game.guest.id)
                or game.guest.name,
                "league_name": self.get_league_name(game.league.id) or game.league.name,
                "goals": len(game.goals),
                "date": self.format_date(game.dateTime, "%Y-%m-%d"),
                "date_short": self.format_date(game.dateTime, "%m/%d"),
                "date_year": self.format_date(game.dateTime, "%Y"),
                "host_score": host_score,
                "guest_score": guest_score,
                "minutes_played": game.minutes,
                "team_name": player_team.name,
                "team_goals": len(game.goals),
                "clear_goal": None,
                "season": game.season,
            }

            if game.minutes > 45 and team_goals[enemy_team.name] == 0:
                parsed_game["clear_goal"] = True
            elif game.minutes > 45 and team_goals[enemy_team.name] != 0:
                parsed_game["clear_goal"] = False

            if team_goals[player_team.name] > team_goals[enemy_team.name]:
                parsed_game["result"] = {"name": "W", "type": "won"}
            elif team_goals[player_team.name] < team_goals[enemy_team.name]:
                parsed_game["result"] = {"name": "P", "type": "lost"}
            else:
                parsed_game["result"] = {"name": "R", "type": "draw"}

            parsed_game["yellow_cards"], parsed_game["red_cards"] = self.resolve_cards(
                game.cards
            )

            games.append(parsed_game)

        games.sort(key=lambda g: g["date"], reverse=True)
        return games


class StatsSerializer(BasePlayerSerializer):
    def __init__(self, stats: PlayerSeasonStatsListSchema) -> None:
        """serializer responsible for preparing stats"""
        self.stats = stats

        if stats and not isinstance(stats[0], PlayerSeasonStatsSchema):
            raise WrongDataFormatException(
                self, PlayerSeasonStatsSchema, type(stats[0])
            )

    @property
    def data(self) -> typing.Dict:
        """get all season stats based on data collected by adapter"""
        return self.parse_season_stats()

    @property
    def data_summary(self) -> typing.Dict:
        """get season summary stats based on data collected by adapter"""
        return self.parse_season_summary_stats()

    def calculate_percentages(self, var: int, total: int) -> float:
        """return float value of percentage"""
        return (var / total) * 100

    def parse_season_summary_stats(
        self, season: str = None
    ) -> typing.Optional[typing.Dict]:
        """get season summary stats based on data collected by adapter"""
        from utils import get_current_season

        if not season:
            season = get_current_season()
        stats_list: PlayerSeasonStatsListSchema = PlayerSeasonStatsListSchema(
            __root__=list(filter(lambda stat: stat.season == season, self.stats))
        )
        if len(stats_list) > 1:
            stats = resolve_stats_list(stats_list)
        elif len(stats_list) == 1:
            stats = stats_list[0]
        else:
            DataShortageLogger(
                obj=self,
                func_name="parse_season_summary_stats()",
                season=season,
            )
            return

        return {
            "bench": stats.substitute,
            "from_bench": stats.substitute_played,
            "first_squad_games_played": stats.played_starter,
            "red_cards": stats.red_cards,
            "yellow_cards": stats.yellow_cards,
            "team_goals": stats.goals,
            "lost_goals": stats.goals_lost or 0,
            "season_name": stats.season,
            "games_played": stats.games_count,
            "bench_percent": self.calculate_percentages(
                stats.substitute, stats.games_count
            ),
            "first_percent": self.calculate_percentages(
                stats.played_starter, stats.games_count
            ),
            "minutes_played": stats.minutes_played,
            "from_bench_percent": self.calculate_percentages(
                stats.substitute_played, stats.games_count
            ),
        }

    def parse_season_stats(self) -> typing.Dict:
        """get all season stats based on data collected by adapter"""
        prepared_stats = {}

        if len(self.stats) < 1:
            DataShortageLogger(
                obj=self, func_name="parse_season_stats()", stats=self.stats.__root__
            )

        for season, stats in groupby(self.stats.__root__, lambda stat: stat.season):
            prepared_stats[season] = {}
            for seq in list(stats):
                league_name = self.get_league_name(seq.league.id) or seq.league.name
                try:
                    prepared_stats[season][league_name]
                except KeyError:
                    prepared_stats[season][league_name] = {}
                team_name = self.resolve_team_name(seq.team.id) or seq.team.name

                prepared_stats[season][league_name][team_name] = {
                    "red_cards": seq.red_cards,
                    "yellow_cards": seq.yellow_cards,
                    "lost_goals": seq.goals_lost,
                    "team_goals": seq.goals,
                    "games_played": seq.games_count,
                    "minutes_played": seq.minutes_played,
                    "first_squad_games_played": seq.played_starter,
                }

        return prepared_stats
