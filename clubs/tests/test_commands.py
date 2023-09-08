from unittest import TestCase

import factory
import pytest
from django.core.management import call_command
from django.db.models import QuerySet

from clubs.management.commands.change_league_seniorty import (
    Command as ChangeLeagueSeniorityCommand,
)
from clubs.models import League, Seniority
from utils.factories import LeagueFactory, SeniorityFactory


@pytest.mark.django_db
class TestChangeLeagueSeniority(TestCase):

    command_name = "change_league_seniorty"
    CENTRAL_JUNIOR_LEAGUE_NAME = "Centralna Liga Juniorow"

    def setUp(self) -> None:
        seniority = SeniorityFactory.create_batch(2)
        self.clj_seniority: Seniority = SeniorityFactory.create(
            name=self.CENTRAL_JUNIOR_LEAGUE_NAME
        )

        leagues_names = [
            "CLJ U-19",
            "Liga Makroregionalna U-19",
            "CLJ U-18",
            "CLJ U-17",
            "CLJ U-15",
            "CLJ U-17 K",
            "CLJ U-15 K",
        ]
        LeagueFactory.create_batch(
            7,
            name=factory.Sequence(lambda n: leagues_names[n % 7]),
            seniority=factory.Sequence(lambda n: seniority[n % 2]),
        )
        self.seniority_command = ChangeLeagueSeniorityCommand()

    def test_call_command(self):
        """
        Test if command change league seniority to "Centralna Liga Juniorow"
        if requires are satisfied
        """
        leagues = League.objects.all()
        assert leagues.count() == 7
        assert (
            leagues.filter(seniority__name=self.CENTRAL_JUNIOR_LEAGUE_NAME).count() == 0
        )

        call_command(self.command_name)
        leagues_refreshed: QuerySet[League] = League.objects.all()
        assert leagues_refreshed.count() == 7
        assert (
            leagues_refreshed.filter(
                seniority__name=self.CENTRAL_JUNIOR_LEAGUE_NAME
            ).count()
            == 7
        )

        for league in leagues:
            assert league.seniority.name == self.CENTRAL_JUNIOR_LEAGUE_NAME

        call_command(self.command_name)
        LeagueFactory.create_batch(2)
        leagues_refreshed2: QuerySet[League] = League.objects.all()
        assert leagues_refreshed2.count() == 9
        assert (
            leagues_refreshed2.filter(
                seniority__name=self.CENTRAL_JUNIOR_LEAGUE_NAME
            ).count()
            == 7
        )

    def test_call_command_no_seniority_object_found(self):
        """Test if command creates new seniority object if it is not found in db"""
        self.clj_seniority.delete()
        call_command(self.command_name)
        assert Seniority.objects.count() == 3
        assert Seniority.objects.filter(name=self.CENTRAL_JUNIOR_LEAGUE_NAME).exists()

    def test_central_league_seniority_method(self):
        """Test if central_league_seniority method returns proper object"""
        result: Seniority = self.seniority_command.central_league_seniority
        assert isinstance(result, Seniority)
        assert result.name == self.CENTRAL_JUNIOR_LEAGUE_NAME

    def test_change_league_seniority(self):
        """Test if change_league_seniority method changes seniority of league objects"""
        leagues = League.objects.all()
        self.seniority_command.change_league_seniority(leagues=leagues)

        for league in leagues:
            assert league.seniority.name == self.CENTRAL_JUNIOR_LEAGUE_NAME

    def test_create_new_central_junior_seniority(self):
        """
        Test if create_new_central_junior_seniority method
        creates new seniority object
        """
        self.clj_seniority.delete()
        self.seniority_command.create_new_central_junior_seniority()
        assert Seniority.objects.count() == 3
        assert Seniority.objects.filter(name=self.CENTRAL_JUNIOR_LEAGUE_NAME).exists()


@pytest.mark.django_db
class TestHidePredefinedLeagues(TestCase):

    command_name = "hide_predefined_leagues"
    LEAGUES_TO_HIDE = [
        "II Liga PLF K",
        "Futsal Ekstraklasa",
        "Liga Makroregionalna U-19",
        "I Liga PLF K",
        "I Liga PLF",
        "II Liga PLF",
        "III Liga PLF",
        "Ekstraliga PLF K",
    ]

    def setUp(self) -> None:
        LeagueFactory.create_batch(
            8, name=factory.Sequence(lambda n: self.LEAGUES_TO_HIDE[n % 8])
        )

    def test_call_command(self):
        """Test if command hides predefined leagues"""
        leagues = League.objects.all()
        assert leagues.count() == 8
        assert leagues.filter(visible=True).count() == 8

        call_command(self.command_name)
        leagues_refreshed: QuerySet[League] = League.objects.all()
        assert leagues_refreshed.count() == 8
        assert leagues_refreshed.filter(visible=True).count() == 0

    def test_call_command_no_league_found(self):
        """Test if command does not raise error if no league is found in db"""
        League.objects.all().delete()
        call_command(self.command_name)
        assert League.objects.count() == 0
