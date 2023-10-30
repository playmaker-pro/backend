import pytest
from django.test import TestCase

from adapters.player_adapter import PlayerScoreAdapter
from adapters.tests.utils import create_seasons, get_adapter
from utils.testutils import create_system_user


@pytest.mark.django_db
class ScoreSerializerUnitTest(TestCase):
    def setUp(self) -> None:
        create_system_user()
        create_seasons()
        self.adapter = get_adapter(PlayerScoreAdapter)
        self.adapter.get_pm_score()
        self.adapter.get_latest_seasons_scores()
        self.serializer = self.adapter.serialize()
        self.data = self.serializer.data

    def test_structure(self) -> None:
        """test structure of serialized scoring"""
        assert self.data["player_id"]
        assert self.data["pm_score"]
        assert self.data["season_score"]

    def test_get_pm_score(self) -> None:
        """test serializer's PlayMaker Score property"""
        attr = self.serializer.player_score
        assert attr and isinstance(attr, int)

    def test_get_season_score(self) -> None:
        """test serializer's Season Score property"""
        attr = self.serializer.player_season_score
        assert attr and isinstance(attr, dict)
