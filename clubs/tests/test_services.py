import datetime
import typing
from unittest import TestCase

from rest_framework.test import APITestCase

from clubs import errors
from clubs.models import Gender, League, Team, TeamHistory
from clubs.services import ClubTeamService, SeasonService, TeamHistoryCreationService
from profiles.api.serializers import PlayerProfileTeamContributorInputSerializer
from roles import definitions
from utils import testutils as utils
from utils.factories import (
    SEASON_NAMES,
    GenderFactory,
    LeagueFactory,
    SeasonFactory,
    TeamFactory,
    UserFactory,
)


class TestClubTeamService(APITestCase):
    def setUp(self) -> None:
        """
        Set up test data.
        """
        male_gender = GenderFactory(name="M")
        female_gender = GenderFactory(name="F")
        TeamFactory(gender=male_gender)
        TeamFactory(gender=female_gender)

    def test_get_clubs(self) -> None:
        """
        Test that `get_clubs` method returns all clubs.
        """
        service = ClubTeamService()
        clubs = service.get_clubs()
        assert clubs.count() == 2

    def test_get_clubs_with_filters(self) -> None:
        """
        Test that `get_clubs` method returns filtered clubs.
        """
        service = ClubTeamService()
        filters = {"gender": "M"}
        clubs = service.get_clubs(filters=filters)
        assert clubs.count() == 1

    def test_validate_gender_valid(self) -> None:
        gender = "M"
        try:
            ClubTeamService.validate_gender(gender)
        except ValueError:
            assert False, "Unexpected ValueError"

    def test_validate_gender_invalid(self) -> None:
        """
        Test that `validate_gender` method does not raise an exception for valid gender.
        """
        invalid_gender = "X"
        try:
            ClubTeamService.validate_gender(invalid_gender)
            assert False, "Expected ValueError but none was raised"
        except ValueError:
            pass


class TestSeasonService(TestCase):
    def test_validate_season_valid(self) -> None:
        """if given season is valid."""
        valid_season = "2020/2021"
        assert SeasonService.is_valid(valid_season)

    def test_validate_season_invalid(self) -> None:
        """if given season is invalid."""

        invalid_season_names = [
            "2020/202",
            "2020/2020",
            "2020/2020/2020",
            "1/1",
            "aa/bb",
            "aaaa/bbbb",
        ]

        for invalid_season_name in invalid_season_names:
            assert not SeasonService.is_valid(invalid_season_name)


class TeamHistoryCreationServicesTest(APITestCase):
    def setUp(self) -> None:
        """Set up test environment."""
        utils.create_system_user()
        self.user = UserFactory.create(
            email="username", declared_role=definitions.PLAYER_SHORT
        )
        self.seasons = [
            SeasonFactory.create(name=season_name) for season_name in SEASON_NAMES
        ]
        self.league = LeagueFactory.create()
        self.service = TeamHistoryCreationService()

    def test_create_or_get_team_with_existing_id(self) -> None:
        """Should retrieve a Team using its existing ID."""
        team = TeamFactory.create()
        validated_data = {
            "team_parameter": team.id,
            "league_identifier": self.league.pk,
        }
        retrieved_team: Team = self.service.get_or_create(
            validated_data, self.user, "PL"
        )
        assert team == retrieved_team

    def test_get_gender_from_data_valid_id(self) -> None:
        """Should retrieve a Gender using its valid ID."""
        gender = GenderFactory.create()
        validated_data: typing.Dict[str, int] = {"gender": gender.id}
        retrieved_gender: Gender = self.service.get_gender_from_data(validated_data)
        assert gender == retrieved_gender

    def test_create_or_get_team_missing_parameters(self) -> None:
        """
        Test the custom behavior of the TeamContributorInputSerializer.

        Specifically, we want to ensure that our custom validation in the
        TeamContributorInputSerializer correctly identifies and reports missing
        fields that are required for the creation or retrieval of a team.
        """
        data = {}
        serializer = PlayerProfileTeamContributorInputSerializer(data=data)
        assert not serializer.is_valid()
        expected_missing_fields = [
            "team_parameter",
            "league_identifier",
            "season",
        ]
        for field in expected_missing_fields:
            assert field in serializer.errors

    def test_create_or_get_team_with_foreign_team_string_parameter(self) -> None:
        """Should retrieve or create a foreign (non-Polish) Team using its string name."""
        gender = GenderFactory.create()
        validated_data = {
            "team_parameter": "Foreign Test Team",
            "country": "IT",
            "gender": gender.id,
        }
        team: Team = self.service.get_or_create(validated_data, self.user, "IT")
        assert team.name == "Foreign Test Team"
        assert team.gender == gender

    def test_create_or_get_team_with_polish_team_string_parameter(self) -> None:
        """Should retrieve or create a Polish Team using its string name."""
        validated_data = {
            "team_parameter": "Polish Test Team",
            "league_identifier": self.league.pk,
            "country": "PL",
        }
        team: Team = self.service.get_or_create(validated_data, self.user, "PL")
        assert team.name == "Polish Test Team"
        assert team.gender == self.league.gender

    def get_or_create_team_by_name_existing_team(self) -> None:
        """Should retrieve an existing Team by its name."""
        team = TeamFactory.create(name="Test Team")
        league = LeagueFactory.create(name="Ekstraklasa", country="PL")
        retrieved_team: Team = self.service.get_or_create_team_by_name(
            team.name, None, league.seniority, self.user
        )
        assert team == retrieved_team

    def test_get_or_create_team_by_name_new_team(self) -> None:
        """Should create a new Team when it doesn't exist and its name is provided."""
        team_name = "Test Team"
        league = LeagueFactory.create(name="Ekstraklasa", country="PL")
        retrieved_team: Team = self.service.get_or_create_team_by_name(
            team_name, None, league.seniority, self.user
        )
        assert retrieved_team.name == team_name

    def test_get_or_create_league_by_name_new_league(self) -> None:
        """Should create a new League when it doesn't exist and its name is provided."""
        league_name = "Premier League"
        gender = GenderFactory.create()
        retrieved_league: League = self.service.create_or_get_league_by_name(
            league_name, "UK", self.user, gender
        )
        assert retrieved_league.name == league_name
        assert retrieved_league.gender == gender

    def test_get_team_by_invalid_id(self):
        """Should raise an error when trying to retrieve a Team with an invalid ID."""
        with self.assertRaises(errors.TeamNotFoundServiceException):
            self.service.get_team_by_id(111111111111111111111111111)

    def test_get_or_create_team_by_name_multiple_invocations(self) -> None:
        """Should ensure that multiple invocations don't create duplicate Teams."""
        team_name = "Test Team"
        league = LeagueFactory.create(name="Ekstraklasa", country="PL")
        self.service.get_or_create_team_by_name(
            team_name, None, league.seniority, self.user
        )
        retrieved_team: Team = self.service.get_or_create_team_by_name(
            team_name, None, league.seniority, self.user
        )
        assert retrieved_team.name == team_name
        assert Team.objects.filter(name=team_name).count() == 1

    def test_create_or_get_team_history_for_player(self):
        """
        Test the functionality of the `create_or_get_team_history_for_player` method.
        """
        season = self.seasons[0]
        team_parameter = "Test Team Parameter"
        league_identifier = self.league.pk
        country_code = "PL"

        assert not TeamHistory.objects.filter(
            team__name=team_parameter,
            league_history__league=self.league,
            season=season,
        ).exists()

        team_history = self.service.create_or_get_team_history_for_player(
            season.id, team_parameter, league_identifier, country_code, self.user
        )

        assert team_history.team.name == team_parameter
        assert team_history.league_history.league == self.league
        assert team_history.season == season

        same_team_history = self.service.create_or_get_team_history_for_player(
            season.id, team_parameter, league_identifier, country_code, self.user
        )

        assert same_team_history.pk == team_history.pk

    def test_create_or_get_team_history_date_based(self):
        # Define the date range (from 2020 to 2022, spanning 3 seasons)
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date(2022, 12, 31)
        team_parameter = "Test Team Parameter"
        league_identifier = self.league.pk
        country_code = "PL"

        # Call the method
        team_histories = self.service.create_or_get_team_history_date_based(
            start_date,
            end_date,
            team_parameter,
            league_identifier,
            country_code,
            self.user,
        )

        assert len(team_histories) == 4

        for th in team_histories:
            assert th.team.name == team_parameter
            assert th.league_history.league == self.league

    def test_create_or_get_team_history_date_based_invalid_dates(self):
        start_date = datetime.date(2022, 1, 1)
        end_date = datetime.date(2020, 12, 31)
        team_parameter = "Test Team Parameter"
        league_identifier = "Test League Identifier"
        country_code = "PL"

        # Assert that an error is raised for invalid date range
        with self.assertRaises(ValueError):
            self.service.create_or_get_team_history_date_based(
                start_date,
                end_date,
                team_parameter,
                league_identifier,
                country_code,
                self.user,
            )
