from django.test import TestCase
from pm_core.services.models.player import PlayerBaseSchema
from pm_core.services.models.models import (
    VoivodeshipSchema,
    TeamSchema,
    BaseLeagueSchema,
)
from adapters.player_adapter import PlayerDataAdapter
from adapters.tests.base import BasePlayerUnitTest
from adapters.tests.factories import _ID


class PlayerDataAdapterUnitTest(TestCase, BasePlayerUnitTest):
    @classmethod
    def setUpClass(cls) -> None:
        super(PlayerDataAdapterUnitTest, cls).setUpClass()
        cls.adapter = cls.define_adapter(PlayerDataAdapter)

    def test_get_player_uuid(self) -> None:
        """test user has uuid"""
        _id = self.adapter.player_uuid
        assert _id == _ID

    def test_player_data(self) -> None:
        """test player data is correct"""
        assert self.adapter.player_data_exists is True
        assert isinstance(self.adapter.data, PlayerBaseSchema)

    def test_get_team(self) -> None:
        """test get player team"""
        team = self.adapter.get_current_team()
        assert isinstance(team, TeamSchema)

    def test_get_voivodeship_with_valid_club(self) -> None:
        """test get player voivo if voivo is in club schema"""
        zpn = self.adapter.get_current_voivodeship()
        assert isinstance(zpn, VoivodeshipSchema)

    def test_get_voivodeship_with_invalid_club(self) -> None:
        """test get player voivo if there is no voivo in club schema"""
        self.adapter.data.club.voivodeship = None
        zpn = self.adapter.get_current_voivodeship()
        assert isinstance(zpn, VoivodeshipSchema)

    def test_get_player_league(self) -> None:
        """test get player league"""
        league = self.adapter.get_current_league()
        assert isinstance(league, BaseLeagueSchema)
