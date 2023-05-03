import pytest
from django.test import TestCase
from pm_core.services.models import PlayerSeasonStatsSchema

from adapters.player_adapter import PlayerSeasonStatsAdapter
from adapters.tests.utils import get_adapter


@pytest.mark.django_db
class PlayerStatsAdapterUnitTest(TestCase):
    def setUp(self) -> None:
        self.adapter = get_adapter(PlayerSeasonStatsAdapter)

    def test_season_stats_structure(self):
        """test season stats structure stored by adapter"""
        self.adapter.get_season_stats(primary_league=False)
        stats = self.adapter.stats

        for stat in stats:
            assert (
                stat.played_starter + stat.substitute_played + stat.substitute
                == stat.games_count
            )
            assert isinstance(stat, PlayerSeasonStatsSchema)

    def test_season_summary_stats_structure(self):
        """test season summary stats structure stored by adapter"""
        self.adapter.get_season_stats()
        stats = self.adapter.stats
        assert isinstance(stats[0], PlayerSeasonStatsSchema)
