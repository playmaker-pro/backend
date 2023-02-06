import typing
from unittest import TestCase
from pm_core.stubs.player_stub import PlayerApiServiceStub
from adapters.tests.factories import (
    MapperEntityFactory,
    PlayerProfileFactory,
)
from adapters.strategy import JustGet
from adapters.player_adapter import PlayerAdapterBase


class BasePlayerUnitTest(TestCase):

    adapter = None
    fake_player = None

    @classmethod
    def setUpClass(cls):
        cls.fake_player = PlayerProfileFactory()
        MapperEntityFactory(target=cls.fake_player.mapper)

    @classmethod
    def define_adapter(cls, adapter: typing.Type[PlayerAdapterBase]):
        return adapter(
            player=cls.fake_player, api_method=PlayerApiServiceStub, strategy=JustGet
        )
