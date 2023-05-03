from unittest import TestCase

import pytest
from pm_core.services.stubs.player_stub import PlayerApiServiceStub

from adapters.tests.utils import dummy_player
from utils.factories.clubs_factories import SeasonFactory
from utils.factories.profiles_factories import PlayerMetricsFactory


@pytest.mark.django_db
class PlayerMetricsTest(TestCase):
    def setUp(self) -> None:
        self.player = dummy_player()
        PlayerMetricsFactory(player=self.player)
        [SeasonFactory() for _ in range(4)]
        self.player.refresh_metrics(PlayerApiServiceStub)
        self.metrics = self.player.playermetrics

    def test_season_stats(self) -> None:
        """test if season is saved correctly"""
        assert isinstance(self.metrics.season, dict)
        assert self.metrics.season is not None
        assert self.metrics.season_updated

    def test_season_summary_stats(self) -> None:
        """test if season summary is saved correctly"""
        assert isinstance(self.metrics.season_summary, dict)
        assert self.metrics.season_summary is not None
        assert self.metrics.season_summary_updated

    def test_games(self) -> None:
        """test if games are saved correctly"""
        assert isinstance(self.metrics.games, list)
        assert self.metrics.games is not None
        assert self.metrics.games_updated

    def test_games_summary(self) -> None:
        """test if games summary is saved correctly"""
        assert isinstance(self.metrics.games_summary, list)
        assert self.metrics.games_summary is not None
        assert self.metrics.games_summary_updated
