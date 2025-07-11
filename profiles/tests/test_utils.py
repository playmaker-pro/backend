from django.test import TestCase
from parameterized import parameterized

from clubs import errors as club_errors
from profiles import errors as errors
from profiles.api import errors as api_errors
from profiles.utils import map_service_exception
from transfers.models import ProfileTransferRequest


class MapServiceExceptionTest(TestCase):
    @parameterized.expand(
        [
            (
                club_errors.LeagueNotFoundServiceException(),
                club_errors.LeagueDoesNotExist,
            ),
            (
                club_errors.LeagueHistoryNotFoundServiceException(),
                club_errors.LeagueHistoryDoesNotExist,
            ),
            (club_errors.TeamNotFoundServiceException(), club_errors.TeamDoesNotExist),
            (
                errors.TeamContributorAlreadyExistServiceException(),
                api_errors.TeamContributorExist,
            ),
            (
                errors.TeamContributorNotFoundServiceException(),
                api_errors.TeamContributorDoesNotExist,
            ),
            (
                club_errors.SeasonDoesNotExistServiceException(),
                club_errors.SeasonDoesNotExist,
            ),
        ],
    )
    def test_mapping_valid_service_exception(
        self, service_exception, expected_api_exception
    ):
        # Test valid service exceptions and see if they are correctly mapped.
        mapped_exception = map_service_exception(service_exception)
        assert mapped_exception == expected_api_exception, (
            f"Failed to map {type(service_exception)} to {expected_api_exception}"
        )

    def test_unmapped_exception_returns_none(self):
        # Test that an exception not in the mapping returns None.
        class DummyException(Exception):
            pass

        dummy_exception_instance = DummyException()
        mapped_exception = map_service_exception(dummy_exception_instance)
        assert mapped_exception is None, "Expected None for unmapped exceptions."


def set_stadion_address(
    transfer_request: ProfileTransferRequest, latitude: float, longitude: float
) -> None:
    """
    Helper method to set latitude and longitude for a Transfer Request
    team's stadion address.
    """
    address = transfer_request.requesting_team.team_history.all()[
        0
    ].club.stadion_address
    address.latitude = latitude
    address.longitude = longitude
    address.save()
    address.refresh_from_db()
