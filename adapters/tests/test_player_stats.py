from django.test import TestCase
from pm_core.services.models import PlayerSeasonStatsSchema

from adapters.player_adapter import PlayerSeasonStatsAdapter
from pm_core.stubs.player_stub import PlayerApiServiceStub
from adapters.strategy import JustGet
from .utils import create_valid_player


class PlayerDataAdapterUnitTest(TestCase):
    def setUp(self) -> None:
        fake_player = create_valid_player()

        self.adapter = PlayerSeasonStatsAdapter(
            fake_player, api_method=PlayerApiServiceStub, strategy=JustGet
        )
        self.stats = self.adapter.get_season_stats()

    def test_structure(self):
        assert (
            self.stats.percentage_substitute
            + self.stats.percentage_substitute_played
            + self.stats.percentage_played_starter
            == 100
        )
        assert isinstance(self.stats, PlayerSeasonStatsSchema)
