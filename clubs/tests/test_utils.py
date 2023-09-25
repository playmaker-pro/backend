import pytest

from clubs.management.commands.utils import generate_club_or_team_short_name
from utils.factories.clubs_factories import (
    ClubFactory,
    LeagueFactory,
    LeagueHistoryFactory,
    TeamFactory,
    TeamHistoryFactory,
)


@pytest.mark.django_db
class TestShortNameCreation:
    @pytest.fixture
    def club_factory(self):
        """
        Provides a factory for creating Club objects.
        """
        return ClubFactory

    @pytest.mark.parametrize(
        "input_name, expected_output",
        [
            ("Basic FC", "FC Basic"),
            ("Club KP", "KP Club"),
            ("TEAM NAME", "Team Name"),
        ],
    )
    def test_basic_name(self, input_name, expected_output, club_factory):
        """
        Test basic name transformations.
        """
        result = generate_club_or_team_short_name(club_factory(name=input_name))
        assert result == expected_output

    @pytest.mark.parametrize(
        "input_name, expected_output",
        [
            ("KP Starogard Gdański", "KP Starogard Gdański"),
            ("Foto-Higiena Błyskawica Gać", "Foto-Higiena Błyskawica Gać"),
        ],
    )
    def test_persistent_name(self, input_name, expected_output, club_factory):
        """
        Test that certain names remain unmodified.
        """
        result = generate_club_or_team_short_name(club_factory(name=input_name))
        assert result == expected_output

    @pytest.mark.parametrize(
        "input_name, expected_output",
        [
            ("Latarnik Choczewo Gtstir", "Latarnik Choczewo"),
            ("Some Club Stowarzyszenie Sportowe", "Some Club"),
            ("UKS SMS Team City", "SMS Team City"),
        ],
    )
    def test_remove_words(self, input_name, expected_output, club_factory):
        """
        Test the removal of specific words from the club name.
        """
        result = generate_club_or_team_short_name(club_factory(name=input_name))
        assert result == expected_output

    def test_futsal_suffix(self, club_factory):
        """
        Test the addition of the futsal suffix for appropriate clubs.
        """
        result = generate_club_or_team_short_name(club_factory(name="Some Futsal Club"))
        assert "Futsal" in result

    @pytest.mark.parametrize(
        "input_name, expected_output",
        [
            ("Latarnik Choczewo 1998 Gtstir", "Latarnik Choczewo"),
            ("1234 Some Club Stowarzyszenie Sportowe", "Some Club"),
            ("UKS SMS Team 2023 City", "SMS Team City"),
        ],
    )
    def test_year_removal(self, input_name, expected_output, club_factory):
        """
        Test that years (four-digit numbers) are removed from club names.
        """
        result = generate_club_or_team_short_name(club_factory(name=input_name))
        assert result == expected_output

    def test_club_with_teams_in_futsal_league(self):
        """
        Test that clubs with all teams playing in the futsal league receive the appropriate futsal suffix.
        """
        # 1. Create a club using the ClubFactory
        club = ClubFactory(name="Wisla Plock", short_name="Wisla Plock")

        # 2. Associate that club with teams playing in the "futsal" league
        futsal_league = LeagueFactory(name="Futsal")
        league_history = LeagueHistoryFactory(league=futsal_league)

        team_1 = TeamFactory(club=club, name="Wisla Plock Team 1")
        team_2 = TeamFactory(club=club, name="Wisla Plock Team 2")

        TeamHistoryFactory(team=team_1, league_history=league_history)
        TeamHistoryFactory(team=team_2, league_history=league_history)
        assert club.name == "Wisla Plock"
        club_short_name = generate_club_or_team_short_name(club)
        # 4. Verify the output
        assert club_short_name == "Wisla Plock (Futsal)"
