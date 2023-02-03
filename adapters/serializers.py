import typing
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from pm_core.services.models import GameSchema, BaseTeamSchema, EventSchema
from adapters.exceptions import ObjectNotFoundException, WrongDataFormatException

from mapper.models import MapperEntity


class GameSerializer:
    def __init__(self, data: typing.List[GameSchema], limit: int = None):
        """
        data - array of games
        limit - determine how many games do you want to get (sort desc by date)
        """
        if not isinstance(data[0], GameSchema):
            raise WrongDataFormatException(self, GameSchema, type(data[0]))

        self.games = data
        self.limit = limit

    def resolve_team_name(self, team_id: str) -> str:
        """get team name from s51"""
        try:
            team_entity = MapperEntity.objects.get(mapper_id=team_id)
        except ObjectDoesNotExist:  # maybe display name from api in case?
            raise ObjectNotFoundException(team_id, BaseTeamSchema)

        return team_entity.target.teamhistory.team.name

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
    def data(self):
        """get serialized list of games (desc sort)"""
        if self.limit:
            return self.parse_games()[: self.limit]
        return self.parse_games()

    def league_name(self, _id: str) -> str:
        """get league name from s51 (scrapper has different league names)"""
        entity = MapperEntity.objects.filter(mapper_id=_id).first()
        if entity:
            return entity.target.league_history.league.highest_parent.name

    def parse_games(self):
        """translate new games data like old serializer"""
        games = []

        for game in self.games:
            final_result = game.scores.final
            player_team = (
                game.host if game.player_current_team == game.host.id else game.guest
            )
            enemy_team = game.guest if player_team is game.host else game.host
            host_score, guest_score = final_result.split(":")

            team_goals = {game.host.name: host_score, game.guest.name: guest_score}

            parsed_game = {
                "host_team_name": game.host.name,
                "guest_team_name": game.guest.name,
                "league_name": self.league_name(game.league.id) or game.league.name,
                "goals": len(game.goals),
                "date": self.format_date(game.dateTime, "%Y-%m-%d"),
                "date_short": self.format_date(game.dateTime, "%m/%d"),
                "date_year": self.format_date(game.dateTime, "%Y"),
                "host_score": host_score,
                "guest_score": guest_score,
                "minutes_played": game.minutes,
                "team_name": player_team.name,
                "team_goals": team_goals[player_team.name],
            }

            if team_goals[player_team.name] > team_goals[enemy_team.name]:
                parsed_game["result"] = {"name": "W", "type": "won"}
            elif team_goals[player_team.name] < team_goals[enemy_team.name]:
                parsed_game["result"] = {"name": "P", "type": "lost"}
            else:
                parsed_game["result"] = {"name": "R", "type": "draw"}

            if game.cards:
                (
                    parsed_game["yellow_cards"],
                    parsed_game["red_cards"],
                ) = self.resolve_cards(game.cards)

            games.append(parsed_game)

        games.sort(key=lambda g: g["date"], reverse=True)
        return games
