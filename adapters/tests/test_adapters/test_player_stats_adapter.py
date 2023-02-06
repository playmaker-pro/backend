from django.test import TestCase
from pm_core.services.models import PlayerSeasonStatsSchema

from adapters.player_adapter import PlayerSeasonStatsAdapter
from adapters.tests.base import BasePlayerUnitTest


class PlayerStatsAdapterUnitTest(TestCase, BasePlayerUnitTest):
    @classmethod
    def setUpClass(cls) -> None:
        super(PlayerStatsAdapterUnitTest, cls).setUpClass()
        cls.adapter = cls.define_adapter(PlayerSeasonStatsAdapter)
        cls.stats = cls.adapter.get_season_stats()

    def test_structure(self):
        assert (
            self.stats.percentage_substitute
            + self.stats.percentage_substitute_played
            + self.stats.percentage_played_starter
            == 100
        )
        assert isinstance(self.stats, PlayerSeasonStatsSchema)
