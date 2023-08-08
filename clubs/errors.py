from api.errors import CoreAPIException
from rest_framework import status


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
