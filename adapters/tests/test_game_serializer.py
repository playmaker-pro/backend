from django.test import TestCase
from pm_core.services.models import EventSchema

from adapters.serializers import GameSerializer
from adapters.player_adapter import PlayerGamesAdapter
from pm_core.stubs.player_stub import PlayerApiServiceStub
from adapters.strategy import JustGet
from .utils import create_valid_player


class GameSerializerUnitTest(TestCase):
    serializer = None
    games = None
    adapter = None

    @classmethod
    def setUpClass(cls):
        super(GameSerializerUnitTest, cls).setUpClass()
        fake_player = create_valid_player()

        cls.adapter = PlayerGamesAdapter(
            fake_player, api_method=PlayerApiServiceStub, strategy=JustGet
        )
        cls.adapter.get_player_games()
        cls.games = cls.adapter.games
        cls.serializer = GameSerializer(cls.games)
        cls.data = cls.serializer.data

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
