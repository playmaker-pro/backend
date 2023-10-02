from django.test import TestCase
from profiles.utils import map_service_exception
from profiles import errors as profile_errors
from clubs import errors as club_errors
from parameterized import parameterized


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
                profile_errors.TeamContributorAlreadyExistServiceException(),
                profile_errors.TeamContributorExist,
            ),
            (
                profile_errors.TeamContributorNotFoundServiceException(),
                profile_errors.TeamContributorDoesNotExist,
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
        assert (
            mapped_exception == expected_api_exception
        ), f"Failed to map {type(service_exception)} to {expected_api_exception}"

    def test_unmapped_exception_returns_none(self):
        # Test that an exception not in the mapping returns None.
        class DummyException(Exception):
            pass

        dummy_exception_instance = DummyException()
        mapped_exception = map_service_exception(dummy_exception_instance)
        assert mapped_exception is None, "Expected None for unmapped exceptions."
