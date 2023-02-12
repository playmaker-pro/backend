from django.test import TestCase
from adapters.player_adapter import PlayerSeasonStatsAdapter
from adapters.tests.utils import get_adapter


class GameSerializerUnitTest(TestCase):
    def setUp(self) -> None:
        self.adapter = get_adapter(PlayerSeasonStatsAdapter)
        self.adapter.get_season_stats()
        self.serializer = self.adapter.serialize()

    def test_calculate_percentages(self):
        """tests the calculation of percentages"""
        assert (self.serializer.calculate_percentages(5, 10)) == 50
        assert (self.serializer.calculate_percentages(0, 10)) == 0
        assert (self.serializer.calculate_percentages(10, 10)) == 100
        assert (self.serializer.calculate_percentages(3, 10)) == 30

    def test_season_summary_stats_structure(self):
        """test structure of serialized season summary stats"""
        self.adapter.get_season_stats()
        serializer = self.adapter.serialize()
        data = serializer.data_summary

        assert (
            data["bench"] + data["from_bench"] + data["first_squad_games_played"]
        ) == data["games_played"]
        assert (
            data["bench_percent"] + data["first_percent"] + data["from_bench_percent"]
        ) == 100
        assert data["minutes_played"] <= data["games_played"] * 90

    def test_season_stats_structure(self):
        """test structure of season stats"""
        self.adapter.get_season_stats(primary_league=False)
        serializer = self.adapter.serialize()
        data = serializer.data

        for _, league in data.items():
            for _, team in league.items():
                stats = list(team.values())[0]
                assert stats["first_squad_games_played"] <= stats["games_played"]
