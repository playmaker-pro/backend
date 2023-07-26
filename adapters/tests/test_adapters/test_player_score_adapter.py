from django.test import TestCase
from adapters.player_adapter import (
    PlayerScoreAdapter,
    PlayerScoreSchema,
    PlayerSeasonScoreListSchema,
)
from adapters.tests.utils import get_adapter
import pytest
from adapters.tests.utils import create_seasons


@pytest.mark.django_db
class PlayerScoreAdapterUnitTest(TestCase):
    def setUp(self) -> None:
        create_seasons()
        self.adapter = get_adapter(PlayerScoreAdapter)
        self.adapter.get_pm_score()
        self.adapter.get_latest_seasons_scores()

    def test_adapter_data_instance(self) -> None:
        """test adapter attrs"""
        assert isinstance(self.adapter.pm_score, PlayerScoreSchema)
        assert isinstance(self.adapter.season_score, PlayerSeasonScoreListSchema)

    def test_stored_all_seasons(self) -> None:
        """Check if all seasons has been stored"""
        assert len(self.adapter.stored_seasons) == 4
        assert len(self.adapter.season_score) == 4

    def test_pm_score_adapter_data(self) -> None:
        """test PlayMaker Score attrs"""
        assert self.adapter.pm_score.player_id
        assert self.adapter.pm_score.value

    def test_season_score_adapter_data(self) -> None:
        """test Season Scores attr"""
        for season_score in self.adapter.season_score:
            assert season_score.player_id
            assert season_score.value
            assert season_score.season_name
