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


class SeasonDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given season does not exist"


class SeasonParameterMissing(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'season' parameter is required."


class InvalidGender(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid Gender, choices: {M, F}"
