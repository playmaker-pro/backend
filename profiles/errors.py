import typing

from rest_framework import status

from api.errors import CoreAPIException


class VerificationCompletionFieldsWrongSetup(Exception):
    pass


class SerializerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidUser(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Request has not defined user or it is incorrect."


class UserAlreadyHasProfile(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Unable to create profile. User already has a profile for given role."
    )


class InvalidProfileRole(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Request has not defined user role or it is incorrect."


class ProfileDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Profile with given UUID does not exist."


class InvalidUUID(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Given UUID is invalid."


class IncompleteRequestBody(CoreAPIException):
    def __init__(self, required_fields: typing.Iterable):
        self.default_detail = (
            f"Incomplete request's body, required fields: {', '.join(required_fields)}"
        )
        super().__init__()

    status_code = status.HTTP_400_BAD_REQUEST


class TooManyAlternatePositionsError(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A player can have a maximum of two alternate positions."


class MultipleMainPositionError(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A player can have only one main position."


class TeamContributorDoesNotExist(CoreAPIException):
    """
    API-specific exception raised when a TeamContributor object is not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Team contributor with given id does not exist."


class TeamContributorExist(CoreAPIException):
    """
    Raised when an API operation attempts to create or add a TeamContributor that already exists.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Team contributor instance with provided values already exist"


class TeamContributorNotFoundServiceException(Exception):
    """
    Raised when a TeamContributor object is not found in service-level functions.
    This is a generic exception meant to signal the absence of a TeamContributor
    """

    pass


class TeamContributorAlreadyExistServiceException(Exception):
    """
    Raised when attempting to create or add a TeamContributor that already
    exists in service-level functions.
    """

    pass


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
    default_detail = ("Voivodeship object is required. "
                      "You should provide voivodeship obj as fallows: voivodeship_obj: {id: 1}")


class LanguageDoesNotExistException(Exception):
    """Raises when language does not exist in DB"""
    ...


class InvalidCoachRoleException(CoreAPIException):
    """
    API HTTP exception raised when a Coach role is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Coach role with given id does not exist."


class InvalidFormationException(CoreAPIException):
    """
    API HTTP exception raised when a given formation is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given formation does not exist."


