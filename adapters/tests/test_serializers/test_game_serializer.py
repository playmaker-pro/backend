import pytest
from django.test import TestCase
from pm_core.services.models import EventSchema

from adapters.player_adapter import PlayerGamesAdapter
from adapters.serializers import GameSerializer
from adapters.tests.utils import get_adapter
from utils.testutils import create_system_user


@pytest.mark.django_db
class GameSerializerUnitTest(TestCase):
    def setUp(self) -> None:
        create_system_user()
        self.adapter = get_adapter(PlayerGamesAdapter)
        self.adapter.clean()
        self.adapter.get_player_games()
        self.games = self.adapter.games
        self.serializer = GameSerializer(self.games)
        self.data = self.serializer.data

    def test_structure(self) -> None:
        """test structure of games"""
        assert len(self.data) == len(self.games)

        for game in self.data:
            result = game["result"]["name"]
            if result in ["W", "P"]:
                assert game["host_score"] != game["guest_score"]
            else:
                assert game["host_score"] == game["guest_score"]

            assert len(game["date"]) == 10
            assert len(game["date_short"]) == 5
            assert len(game["date_year"]) == 4

    def test_sort_by_date(self) -> None:
        """test sort games desc by date"""
        assert self.data[0]["date"] > self.data[1]["date"]
        assert self.data[-2]["date"] > self.data[-1]["date"]

    def test_date_formatter(self) -> None:
        """test date is formatted correctly"""
        date = "09/17/2022 12:30:00"
        _format = self.serializer.format_date
        assert _format(date, "%M") == "30"
        assert _format(date, "%Y") == "2022"
        assert _format(date, "%d") == "17"
        assert _format(date, "%m") == "09"
        assert _format(date, "%H") == "12"

    def test_resolving_cards(self) -> None:
        """test cards are resolving corectly"""
        cards_example = [
            {"type": "Yellow", "minute": 3},
            {"type": "Yellow", "minute": 67},
            {"type": "Red", "minute": 67},
        ]
        cards = [EventSchema(**card) for card in cards_example]
        yellow, red = self.serializer.resolve_cards(cards)
        assert yellow == 2 and red == 1
