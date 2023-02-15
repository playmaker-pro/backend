import typing
from pm_core.services.models import (
    PlayerBaseSchema,
    TeamSchema,
    BaseLeagueSchema,
    GameSchema,
    EventSchema,
    PlayerSeasonStatsSchema,
)
from pm_core.services.models.consts import ExcludedLeague, DEFAULT_LEAGUE_EXCLUDE
from clubs.models import Season
from .serializers import GameSerializer, StatsSerializer
from mapper.models import Mapper
from profiles.models import PlayerProfile
from utils import get_current_season
from .exceptions import (
    PlayerHasNoMapperException,
    PlayerMapperEntityNotFoundException,
    ObjectNotFoundException,
)
from .base_adapter import BaseAdapter
import logging
from django.core.exceptions import ObjectDoesNotExist
from .utils import resolve_stats_list

logger = logging.getLogger(__name__)
LATEST_SEASONS = Season.objects.all().order_by("-name")[:4]


class PlayerAdapterBase(BaseAdapter):
    def __init__(self, player: PlayerProfile, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player: PlayerProfile = player

    def get_player_mapper(self) -> Mapper:
        """
        get mapper object from player
        """
        try:
            return self.player.mapper
        except ObjectDoesNotExist:
            raise PlayerHasNoMapperException(self.player.user.id)

    def get_player_data(self) -> PlayerBaseSchema:
        """
        Get player data
        """
        params = self.resolve_strategy()
        obj = self.api.get_player_data(self.player_uuid, params)

        if not obj:
            raise ObjectNotFoundException(self.player_uuid, PlayerBaseSchema)

        return obj

    @property
    def player_uuid(self) -> str:
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
            raise PlayerMapperEntityNotFoundException(self.player.user.id, params)

        return mapper_entity.mapper_id


class PlayerDataAdapter(PlayerAdapterBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data: PlayerBaseSchema = self.get_player_data()

    def get_current_team(self) -> TeamSchema:
        """
        Get more information about player's team
        """
        params = self.resolve_strategy()
        team_id = self.data.team_id
        obj = self.api.get_team_data(team_id, params)

        if not obj:
            raise ObjectNotFoundException(team_id, PlayerBaseSchema)

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

    games: typing.List[GameSchema] = []

    def get_player_games(
        self,
        season: str = get_current_season(),
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> None:
        """get player games based on season"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season.replace("/", "%2F")
        params["exclude_leagues"] = "+".join([league.name for league in exlude_leagues])
        games = self.api.get_player_participant_games(
            player_id=player_id, params=params
        )

        if not games:
            raise ObjectNotFoundException(player_id, GameSchema)

        self.games += games
        self.unique()
        self.clean_game_minutes()

    def unique(self):
        """filter unique games object from array"""
        unique_ids = []
        unique_objects = []
        for game in self.games:
            if game.matchId not in unique_ids:
                unique_objects.append(game)
                unique_ids.append(game.matchId)
        self.games = unique_objects

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
        for game in self.games:
            self.parse_events_time(game)

            if not game.minutes:
                game.minutes = self.resolve_minutes_on_substitutions(game.substitutions)

            if game.minutes > 90:
                game.minutes = 90

    def serialize(self, limit: int = None) -> GameSerializer:
        """serialize games data, set limit(int) to limitate games count"""
        return GameSerializer(self.games, limit)

    def clean(self) -> None:
        """clear cached games data"""
        self.games = []


class PlayerSeasonStatsAdapter(PlayerAdapterBase):

    stats: typing.List[PlayerSeasonStatsSchema] = []

    def get_season_stats(
        self,
        season: str = get_current_season(),
        primary_league: bool = True,
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> None:
        """get predefined player stats"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season.replace("/", "%2F")
        params["exclude_leagues"] = "+".join([league.name for league in exlude_leagues])

        data = self.api.get_player_season_stats(player_id=player_id, params=params)

        if not data:
            raise ObjectNotFoundException(player_id, PlayerSeasonStatsSchema)

        if primary_league:
            self.stats += [resolve_stats_list(data)]
        else:
            self.stats += data

        self.unique()

    def unique(self):
        """filter unique stats object from array"""
        unique_ids = []
        unique_objects = []
        for stat in self.stats:
            if stat.team.id not in unique_ids:
                unique_objects.append(stat)
                unique_ids.append(stat.team.id)
        self.stats = unique_objects

    def get_latest_seasons_stats(self, primary_league: bool = True) -> None:
        """get stats from last 4 seasons"""
        for season in LATEST_SEASONS:
            self.get_season_stats(season.name, primary_league)

    def serialize(self) -> StatsSerializer:
        """Serialize stored by adapter stats"""
        return StatsSerializer(self.stats)

    def clean(self) -> None:
        """clear cached games data"""
        self.stats = []
