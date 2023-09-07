from rest_framework.test import APITestCase

from clubs.services import ClubTeamService
from utils.factories import GenderFactory, TeamFactory


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
