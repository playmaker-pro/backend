import pytest
from django.test import TestCase
from pm_core.services.models import (
    BaseLeagueSchema,
    BaseTeamSchema,
    EventSchema,
    GameScoreSchema,
)

from adapters.player_adapter import PlayerGamesAdapter
from adapters.tests.utils import get_adapter


@pytest.mark.django_db
class PlayerGamesAdapterUnitTest(TestCase):
    def setUp(self) -> None:
        self.adapter = get_adapter(PlayerGamesAdapter)
        self.adapter.get_player_games()
        self.games = self.adapter.games

    def test_games_structure(self):
        """test games structure"""
        assert all(isinstance(game.league, BaseLeagueSchema) for game in self.games)
        assert all(isinstance(game.host, BaseTeamSchema) for game in self.games)
        assert all(isinstance(game.guest, BaseTeamSchema) for game in self.games)
        assert all(isinstance(game.scores, GameScoreSchema) for game in self.games)
        assert all(game.minutes is not None for game in self.games)
        assert all(90 >= game.minutes >= 0 for game in self.games)
        assert all(isinstance(game.scores, GameScoreSchema) for game in self.games)

    def test_minutes_on_substitutions(self):
        subs_example = [
            EventSchema(**sub)
            for sub in [
                {"type": "In", "minute": 41},
                {"type": "Out", "minute": 86},
            ]
        ]
        just_in = [subs_example[0]]
        just_out = [subs_example[1]]

        test_a = self.adapter.resolve_minutes_on_substitutions(subs_example)
        test_b = self.adapter.resolve_minutes_on_substitutions(just_in)
        test_c = self.adapter.resolve_minutes_on_substitutions(just_out)

        assert test_a == 45
        assert test_b == 49
        assert test_c == 86
