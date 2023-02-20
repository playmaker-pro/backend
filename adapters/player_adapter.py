import typing

from pm_core.services.errors import ServiceRaisedException
from pm_core.services.models import (
    PlayerBaseSchema,
    TeamSchema,
    BaseLeagueSchema,
    GameSchema,
    EventSchema,
    PlayerSeasonStatsListSchema,
    GamesSchema,
)
from pm_core.services.models.consts import ExcludedLeague, DEFAULT_LEAGUE_EXCLUDE
from clubs.models import Season
from .serializers import GameSerializer, StatsSerializer
from mapper.models import Mapper
from utils import get_current_season
from .exceptions import (
    PlayerHasNoMapperException,
    PlayerMapperEntityNotFoundLogger,
    DataShortageLogger,
)
from .base_adapter import BaseAdapter
import logging
from django.core.exceptions import ObjectDoesNotExist
from .utils import resolve_stats_list

logger = logging.getLogger(__name__)
LATEST_SEASONS = Season.objects.all().order_by("-name")[:4]


class PlayerAdapterBase(BaseAdapter):
    data: PlayerBaseSchema = None

    def __init__(self, player, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player = player

    def get_player_mapper(self) -> Mapper:
        """
        get mapper object from player
        """
        try:
            return self.player.mapper
        except ObjectDoesNotExist:
            raise PlayerHasNoMapperException(self.player.user.id)

    def get_player_data(self) -> typing.Optional[DataShortageLogger]:
        """
        Get player data
        """
        params = self.resolve_strategy()
        try:
            obj = self.api.get_player_data(self.player_uuid, params)
        except ServiceRaisedException:
            return DataShortageLogger(
                self, "get_player_data()", player_id=self.player_uuid, params=params
            )

        self.data: PlayerBaseSchema = obj

    @property
    def player_uuid(self) -> typing.Optional[str]:
        """
        uuid straight from LNP
        """
        mapper = self.get_player_mapper()
        params = {
            "database_source": "scrapper_mongodb",
            "related_type": "player",
        }
        mapper_entity = mapper.get_entity(**params)
        if not mapper_entity:
            PlayerMapperEntityNotFoundLogger(self.player.user.id, params)
            return

        return mapper_entity.mapper_id


class PlayerDataAdapter(PlayerAdapterBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_current_team(self) -> typing.Union[TeamSchema, DataShortageLogger]:
        """
        Get more information about player's team
        """
        params = self.resolve_strategy()
        team_id = self.data.team_id
        try:
            obj = self.api.get_team_data(team_id, params)
        except ServiceRaisedException:
            return DataShortageLogger(
                self, "get_current_team()", team_id=team_id, params=params
            )

        return obj

    def get_current_league(self) -> BaseLeagueSchema:
        """
        Get current player's league
        """
        current_team = self.get_current_team()
        return current_team.league

    def get_current_voivodeship(self):
        """
        Get current voivodeship
        """
        zpn = self.data.club.voivodeship

        if not zpn:
            params = self.resolve_strategy()
            club_data = self.api.get_club_data(self.data.club.id, params)
            zpn = club_data.voivodeship

        return zpn

    @property
    def player_data_exists(self) -> bool:
        """
        Check if player data exists
        """
        return bool(self.data)


class PlayerGamesAdapter(PlayerAdapterBase):

    games: GamesSchema = GamesSchema(__root__=[])

    def get_player_games(
        self,
        season: str = get_current_season(),
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> None:
        """get player games based on season"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season
        params["exclude_leagues"] = "+".join([league.name for league in exlude_leagues])
        games = []

        try:
            games = self.api.get_player_participant_games(
                player_id=player_id, params=params
            )
        except ServiceRaisedException:
            DataShortageLogger(
                self, "get_player_games()", player_id=player_id, params=params
            )

        self.games.__root__ += games
        self.unique()
        self.clean_game_minutes()

    def unique(self):
        """filter unique games object from array"""
        unique_ids = []
        unique_objects = []
        for game in self.games.__root__:
            if game.matchId not in unique_ids:
                unique_objects.append(game)
                unique_ids.append(game.matchId)
        self.games.__root__ = unique_objects

    def get_latest_seasons_player_games(self):
        """get games from last 4 seasons"""
        for season in LATEST_SEASONS:
            self.get_player_games(season.name)

    def parse_events_time(self, game: GameSchema):
        """remove ' sign from timestamps presented on events by lnp"""
        event_types = (game.cards, game.goals, game.substitutions)

        for event_list in event_types:
            if event_list:
                for event in event_list:
                    event.minute = str(event.minute).split("+")[0]
                    event.minute = int(str(event.minute).replace("'", ""))

    def resolve_minutes_on_substitutions(
        self, substitutions: typing.List[EventSchema]
    ) -> int:
        """resolve timestamps of player substitutions"""
        _in, _out = None, None
        for sub in substitutions:
            if sub.type == "In":
                _in = int(sub.minute)
            elif sub.type == "Out":
                _out = int(sub.minute)

        if _in and _out:
            return _out - _in
        if _in:
            return 90 - _in
        if _out:
            return _out

    def clean_game_minutes(self) -> None:
        """reformat each played by player game minutes"""
        for game in self.games.__root__:
            self.parse_events_time(game)

            if game.minutes is None:
                game.minutes = self.resolve_minutes_on_substitutions(game.substitutions)

            if game.minutes > 90:
                game.minutes = 90

    def serialize(self, limit: int = None) -> GameSerializer:
        """serialize games data, set limit(int) to limitate games count"""
        serializer = GameSerializer(self.games.copy(), limit)
        self.clean()

        return serializer

    def clean(self) -> None:
        """clear cached games data"""
        self.games.__root__ = []


class PlayerSeasonStatsAdapter(PlayerAdapterBase):

    stats: PlayerSeasonStatsListSchema = PlayerSeasonStatsListSchema(__root__=[])

    def get_season_stats(
        self,
        season: str = get_current_season(),
        primary_league: bool = True,
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> typing.Optional[DataShortageLogger]:
        """get predefined player stats"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season
        params["exclude_leagues"] = "+".join([league.name for league in exlude_leagues])
        try:
            data = self.api.get_player_season_stats(player_id=player_id, params=params)
        except ServiceRaisedException:
            return DataShortageLogger(
                self, "get_season_stats()", player_id=player_id, params=params
            )

        if primary_league:
            self.stats.__root__ += [resolve_stats_list(data)]
        else:
            self.stats.__root__ += data

        self.unique()

    def unique(self):
        """filter unique stats object from array"""
        unique_ids = []
        unique_objects = []
        for stat in self.stats.__root__:
            if stat.team.id not in unique_ids:
                unique_objects.append(stat)
                unique_ids.append(stat.team.id)
        self.stats.__root__ = unique_objects

    def get_latest_seasons_stats(self, primary_league: bool = True) -> None:
        """get stats from last 4 seasons"""
        for season in LATEST_SEASONS:
            self.get_season_stats(season.name, primary_league)

    def serialize(self) -> StatsSerializer:
        """Serialize stored by adapter stats"""
        serializer = StatsSerializer(self.stats.copy())
        self.clean()

        return serializer

    def clean(self) -> None:
        """clear cached games data"""
        self.stats.__root__ = []
