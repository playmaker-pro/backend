from rest_framework import status

from api.errors import CoreAPIException


class TeamDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given team does not exist."


class ClubDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given club does not exist."


class TeamHistoryDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given team history does not exist."


class InvalidSeasonFormatException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid season format"


class InvalidCurrentSeasonFormatException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid current_season format. Should be 'true' or 'false'."


class SeasonDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given season does not exist"


class SeasonParameterMissing(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'season' parameter is required."


class BothSeasonsGivenException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You can only set current_season or specific season, not both."


class InvalidGender(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid Gender, choices: {M, F}"


class TeamAlreadyExist(CoreAPIException):
    """
    Raised when attempting to create or associate a team that already exists.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This team already exist"


class LeagueHistoryDoesNotExist(CoreAPIException):
    """
    Raised when the expected LeagueHistory entity, for a given season and league, is not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "League history not found for given season and league."


class LeagueDoesNotExist(CoreAPIException):
    """
    Raised when a queried League entity is not found in the system.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given league does not exist"


class LeagueNotFoundServiceException(Exception):
    """
    Raised by service-level methods when a League entity is queried but not found.
    """

    pass


class LeagueHistoryNotFoundServiceException(Exception):
    """
    Raised by service-level methods when a LeagueHistory entity is queried but not found.
    """

    pass


class TeamNotFoundServiceException(Exception):
    """
    Raised by service-level functions when a Team entity is sought but not located.
    """

    pass


class SeasonDoesNotExistServiceException(Exception):
    """
    Raised in service-level methods when an expected Season entity is not retrievable.
    """

    pass
