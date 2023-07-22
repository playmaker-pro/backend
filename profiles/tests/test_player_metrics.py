from unittest import TestCase
import pytest
from pm_core.services.stubs.player_stub import PlayerApiServiceStub
from adapters.tests.utils import dummy_player
from utils.factories import SeasonFactory, PlayerMetricsFactory


@pytest.mark.django_db
class PlayerMetricsTest(TestCase):
    def setUp(self) -> None:
        self.player = dummy_player()
        SeasonFactory.create_batch(4)
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

    def test_score(self) -> None:
        """test if scoring is saved correctly"""
        self.player.refresh_scoring(PlayerApiServiceStub)

        assert isinstance(self.metrics.pm_score, int)
        assert self.metrics.pm_score
        assert self.metrics.pm_score_updated

        assert isinstance(self.metrics.season_score, dict)
        assert self.metrics.season_score is not None
        assert self.metrics.season_score_updated

    def test_update_pm_score_only(self) -> None:
        """Test update PlayMaker Score only"""
        assert self.metrics.pm_score is None
        self.metrics.get_and_update_pm_score(PlayerApiServiceStub)
        assert self.metrics.pm_score

    def test_update_season_score_only(self) -> None:
        """Test update Season Score only"""
        assert self.metrics.season_score is None
        self.metrics.get_and_update_season_score(PlayerApiServiceStub)
        assert self.metrics.season_score
