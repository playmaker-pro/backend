import logging
import typing

from django.core.exceptions import ObjectDoesNotExist
from pm_core.services.errors import ServiceRaisedException
from pm_core.services.models import (
    BaseLeagueSchema,
    EventSchema,
    GameSchema,
    GamesSchema,
    PlayerBaseSchema,
    PlayerScoreSchema,
    PlayerSeasonStatsListSchema,
    PlayerSeasonScoreListSchema,
    TeamSchema,
)
from pm_core.services.models.consts import DEFAULT_LEAGUE_EXCLUDE, ExcludedLeague
from requests.exceptions import ConnectionError

from mapper.models import Mapper

from .base_adapter import BaseAdapter
from .exceptions import (
    DataShortageLogger,
    PlayerHasNoMapperException,
    PlayerMapperEntityNotFoundLogger,
    ScrapperIsNotRespongingLogger,
)
from .serializers import GameSerializer, StatsSerializer, ScoreSerializer
from .utils import resolve_stats_list

logger = logging.getLogger(__name__)
NO_CONNECTION_LOG = ScrapperIsNotRespongingLogger()


class PlayerAdapterBase(BaseAdapter):
    data: PlayerBaseSchema = None

    def __init__(self, player, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player = player
        self.season_range = self.get_season_range()

    def get_season_range(self):
        from clubs.models import Season

        return Season.objects.all().order_by("-name")[:4]

    @property
    def current_season(self) -> str:
        """Get current season"""
        from utils import get_current_season

        return get_current_season()

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
        except ConnectionError:
            NO_CONNECTION_LOG()
            return None

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

    def get_current_team(
        self,
    ) -> typing.Optional[typing.Union[TeamSchema, DataShortageLogger]]:
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
        except ConnectionError:
            NO_CONNECTION_LOG()
            return None

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
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.games: GamesSchema = GamesSchema()

    def get_player_games(
        self,
        season: str = None,
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> None:
        """get player games based on season"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season
        params["excluded_leagues"] = " ".join(
            [league.name for league in exlude_leagues]
        )
        games = []

        try:
            games = self.api.get_player_participant_games(
                player_id=player_id, params=params
            )
        except ServiceRaisedException:
            DataShortageLogger(
                self, "get_player_games()", player_id=player_id, params=params
            )
        except ConnectionError:
            NO_CONNECTION_LOG()
            return None

        if not games:
            return

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
        for season in self.season_range:
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
                game.minutes = (
                    self.resolve_minutes_on_substitutions(game.substitutions) or 90
                )

            if game.minutes > 90:
                game.minutes = 90

    def serialize(self, limit: int = None) -> GameSerializer:
        """serialize games data, set limit(int) to limitate games count"""
        return GameSerializer(self.games, limit)

    def clean(self) -> None:
        """clear cached games data"""
        self.games.__root__ = []


class PlayerSeasonStatsAdapter(PlayerAdapterBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.stats: PlayerSeasonStatsListSchema = PlayerSeasonStatsListSchema()

    def get_season_stats(
        self,
        season: str = None,
        primary_league: bool = True,
        exlude_leagues: typing.List[ExcludedLeague] = DEFAULT_LEAGUE_EXCLUDE,
    ) -> typing.Optional[DataShortageLogger]:
        """get predefined player stats"""
        player_id = self.player_uuid
        params = self.resolve_strategy()
        params["season"] = season or self.current_season
        params["excluded_leagues"] = " ".join(
            [league.name for league in exlude_leagues]
        )

        try:
            data = self.api.get_player_season_stats(player_id=player_id, params=params)
        except ServiceRaisedException:
            return DataShortageLogger(
                self, "get_season_stats()", player_id=player_id, params=params
            )
        except ConnectionError:
            NO_CONNECTION_LOG()
            return None

        if not data:
            return

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
        for season in self.season_range:
            self.get_season_stats(season.name, primary_league)

    def serialize(self) -> StatsSerializer:
        """Serialize stored by adapter stats"""
        return StatsSerializer(self.stats)

    def clean(self) -> None:
        """clear cached games data"""
        self.stats.__root__ = []


class PlayerScoreAdapter(PlayerAdapterBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pm_score: typing.Optional[PlayerScoreSchema] = None
        self.season_score: PlayerSeasonScoreListSchema = PlayerSeasonScoreListSchema()

    def get_pm_score(self) -> None:
        """
        Prepare params and call service to get PlayMaker Score.
        Log if something went wrong.
        """
        params = self.resolve_strategy()

        try:
            self.pm_score = self.api.get_pm_score(
                player_id=self.player_uuid, params=params
            )
        except ServiceRaisedException:
            DataShortageLogger(
                self, "get_pm_score()", player_id=self.player_uuid, params=params
            )
        except ConnectionError:
            NO_CONNECTION_LOG()

    def get_season_score(self, season: str = None) -> None:
        """
        Prepare params and call service to get Season Score.
        Log if something went wrong.
        """
        params = self.resolve_strategy()
        params["season"] = season or self.current_season

        try:
            season_score = self.api.get_season_score(
                player_id=self.player_uuid, params=params
            )

            if season_score.season_name not in self.stored_seasons:
                self.season_score.__root__.append(season_score)
        except ServiceRaisedException:
            DataShortageLogger(
                self, "get_season_score()", player_id=self.player_uuid, params=params
            )
        except ConnectionError:
            NO_CONNECTION_LOG()

    def get_latest_seasons_scores(self) -> None:
        """get player season scores from last 4 seasons"""
        for season in self.season_range:
            self.get_season_score(season.name)

    def serialize(self) -> ScoreSerializer:
        """Return serializer based on data collected by adapter"""
        return ScoreSerializer(self.pm_score, self.season_score)

    @property
    def stored_seasons(self) -> typing.List[str]:
        """get list of already collected seasons within season scores"""
        return [season_score.season_name for season_score in self.season_score]

    def get_scoring(self) -> None:
        """
        Method used to fetch everything related with scoring for player
        """
        # Add here new getters related to scoring
        self.get_pm_score()
        self.get_latest_seasons_scores()
