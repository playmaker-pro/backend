from unittest import TestCase

import factory
import pytest
from django.core.management import call_command
from django.db.models import QuerySet

from clubs.management.commands.change_league_seniorty import (
    Command as ChangeLeagueSeniorityCommand,
)
from clubs.models import League, Seniority
from utils.factories import (
    ClubFactory,
    LeagueFactory,
    LeagueHistoryFactory,
    SeniorityFactory,
    TeamFactory,
    TeamHistoryFactory,
)


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


@pytest.mark.django_db
class TestShortNameCommand(TestCase):
    def setUp(self):
        """
        Set up testing environment with various clubs and teams using factories.
        This setup creates different scenarios of club and team names to validate
        the functionality of the short name creation logic.

        Specific patterns like years, prefixes, and hyphens are chosen because they
        are common in club names and have distinct handling rules in the short
        name logic.
        """
        self.league = LeagueFactory.create(
            name="Futsal"
        )  # Use "Futsal" as it's a key term that affects short name generation
        self.league_history = LeagueHistoryFactory.create(league=self.league)

        self.club_with_year = ClubFactory(
            name="Example Club With Year 1998"
        )  # Test removal of years in club names
        self.club_with_prefix_wrong_order = ClubFactory(
            name="CLUB FC"
        )  # Test rearranging prefixes
        self.club_with_hyphen = ClubFactory(
            name="Example-brand Club"
        )  # Test handling of hyphens
        self.club_with_hyphen_in_city_name = ClubFactory(
            name="Kędzierzyn-Koźle Club"
        )  # Ensure cities with hyphens are handled correctly
        self.futsal_club = ClubFactory(
            name="Example Club"
        )  # Ensure cities with hyphens are handled correctly
        self.primary_team = TeamFactory(
            name="Example Team 1998", club=self.club_with_year
        )  # Test suffix addition for clubs in the "Futsal" league
        self.secondary_team = TeamFactory(
            name="Example Team II", club=self.club_with_year
        )
        self.futsal_team = TeamFactory(
            name="Example Futsal Team",
            club=self.futsal_club,
        )
        self.futsal_team_history_factory = TeamHistoryFactory(
            team=self.futsal_team, league_history=self.league_history
        )

    def test_command_output(self):
        """
        Test the correctness of the short name generation logic by checking the output
        of the "create_short_name_for_club_and_team" command. This test focuses
        on predefined scenarios, ensuring that names with specific patterns are
        processed as expected.
        """
        call_command("create_short_name_for_club_and_team")

        # Refresh the objects from the database
        self.club_with_year.refresh_from_db()
        self.club_with_prefix_wrong_order.refresh_from_db()
        self.club_with_hyphen.refresh_from_db()
        self.club_with_hyphen_in_city_name.refresh_from_db()
        self.futsal_club.refresh_from_db()
        self.primary_team.refresh_from_db()
        self.secondary_team.refresh_from_db()
        self.futsal_team.refresh_from_db()

        # Assertions
        assert self.club_with_year.short_name == "Example Club With Year"
        assert self.club_with_prefix_wrong_order.short_name == "FC Club"
        assert self.club_with_hyphen.short_name == "Example Club"
        assert self.club_with_hyphen_in_city_name.short_name == "Kędzierzyn-Koźle Club"
        assert self.futsal_club.short_name == "Example Club (Futsal)"
        assert self.primary_team.short_name == "Example Club With Year"
        assert self.secondary_team.short_name == "Example Club With Year II"
        assert self.futsal_team.short_name == "Example Club"

    def test_random_names(self):
        """
        Test the robustness of the short name generation logic using randomly generated
        club and team names.
        Note: For teams, the short name is based on its associated club's name
        and not the team's own name.
        The goal is to ensure that, even with unexpected input, the generated
        short names adhere to certain standards.
        """
        clubs = ClubFactory.create_batch(20)
        teams = TeamFactory.create_batch(20)

        call_command("create_short_name_for_club_and_team")

        for club in clubs:
            club.refresh_from_db()
            assert club.short_name  # ensure it's not an empty string
            assert len(club.short_name) <= len(
                club.name
            )  # ensure it's shorter or equal to the original name

        for team in teams:
            team.refresh_from_db()
            assert team.short_name  # ensure it's not an empty string
            assert len(team.short_name) <= len(
                team.club.name
            )  # ensure the team's short name is shorter or equal to its club's name
