from rest_framework import status

from api.errors import CoreAPIException


class VerificationCompletionFieldsWrongSetup(Exception):
    pass


class SerializerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TeamContributorNotFoundServiceException(Exception):
    """
    Raised when a TeamContributor object is not found in service-level functions.
    This is a generic exception meant to signal the absence of a TeamContributor
    """


class TeamContributorAlreadyExistServiceException(Exception):
    """
    Raised when attempting to create or add a TeamContributor that already
    exists in service-level functions.
    """

    default_detail = (
        "Voivodeship object is required. "
        "You should provide voivodeship obj as fallows: voivodeship_obj: {id: 1}"
    )


class VoivodeshipDoesNotExistHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a Voivodeship is not found in DB.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Voivodeship with given id does not exist."


class VoivodeshipWrongSchemaHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a Voivodeship update schema is invalid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = (
        "Voivodeship object is required. "
        "You should provide voivodeship obj as fallows: voivodeship_obj: {id: 1}"
    )


class LanguageDoesNotExistException(Exception):
    """Raises when language does not exist in DB"""


class ExpectedIntException(Exception):
    """Raises when given value is not an int"""


class InvalidCoachRoleException(CoreAPIException):
    """
    API HTTP exception raised when a Coach role is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Coach role with given id does not exist."


class InvalidClubRoleException(CoreAPIException):
    """
    API HTTP exception raised when a Coach role is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Club role with given id does not exist."


class InvalidFormationException(CoreAPIException):
    """
    API HTTP exception raised when a given formation is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given formation does not exist."


class InvalidLanguagesListException(CoreAPIException):
    """
    API HTTP exception raised when a given formation is not valid.
    """

    status_code = status.HTTP_400_BAD_REQUEST


class InvalidCitizenshipListException(CoreAPIException):
    """
    API HTTP exception raised when a given formation is not valid.
    """

    status_code = status.HTTP_400_BAD_REQUEST
