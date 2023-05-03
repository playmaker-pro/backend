import typing

from pm_core.services.stubs.player_stub import PlayerApiServiceStub

from adapters.player_adapter import (
    PlayerDataAdapter,
    PlayerGamesAdapter,
    PlayerSeasonStatsAdapter,
)
from adapters.strategy import JustGet
from utils.factories.mapper_factories import MapperEntityFactory
from utils.factories.profiles_factories import PlayerProfileFactory

PLAYER_DEFAULT_TYPEHINT = typing.Union[
    PlayerSeasonStatsAdapter, PlayerDataAdapter, PlayerGamesAdapter
]


def dummy_player():
    player = PlayerProfileFactory()
    MapperEntityFactory(target=player.mapper)
    return player


def get_adapter(
    adapter: typing.Type[PLAYER_DEFAULT_TYPEHINT],
) -> PLAYER_DEFAULT_TYPEHINT:
    return adapter(
        player=dummy_player(),
        api_method=PlayerApiServiceStub,
        strategy=JustGet,
    )
