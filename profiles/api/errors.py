import typing

from rest_framework import status

from api.errors import CoreAPIException
from roles.definitions import PROFILE_TYPE_MAP


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
    Raised when an API operation attempts to create or
    add a TeamContributor that already exists.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Team contributor instance with provided values already exist"


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


class IncorrectProfileRole(CoreAPIException):
    """
    API HTTP exception raised when a given role is not valid.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Invalid role. Must be one of: {list(PROFILE_TYPE_MAP.keys())}."


class InvalidCoachRoleException(CoreAPIException):
    """
    API HTTP exception raised when a Coach role is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Coach role with given id does not exist."


class InvalidCustomCoachRoleException(CoreAPIException):
    """
    API HTTP exception raised when the custom coach role is set
    without the coach role being 'Other' (Inne).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Custom coach role can only be set when coach role is 'Other' (Inne)."
    )


class InvalidFormationException(CoreAPIException):
    """
    API HTTP exception raised when a given formation is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given formation does not exist."


class InvalidSearchTerm(CoreAPIException):
    """
    Custom exception raised when the provided search term
    doesn't meet the specified criteria.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Please provide a search term with at least 3 letters."


class InvalidClubRoleException(CoreAPIException):
    """
    API HTTP exception raised when a Club role is not valid.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Club role does not exist."


class InvalidCustomClubRoleException(CoreAPIException):
    """
    API HTTP exception raised when the custom club role is set
    without the club role being 'Other' (Inne).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Custom club role can only be set when club role is 'Other' (Inne)."
    )


class PermissionDeniedHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a user doesn't have permission to perform an action.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."


class TransferStatusDoesNotExistHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a ProfileTransferStatus is not found in DB.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given player does not have transfer status."


class TransferStatusAlreadyExistsHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a ProfileTransferStatus already exists in DB.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Transfer status for specified user already exists."


class TransferRequestAlreadyExistsHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a ProfileTransferRequest already exist in DB.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Transfer request for specified user already exists."


class TransferRequestDoesNotExistHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a ProfileTransferRequest is not found in DB.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given player does not have transfer request."


class NotAOwnerOfTheTeamContributorHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a user is not a owner of the team contributor.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You can't request transfer for this team."


class PhoneNumberMustBeADictionaryHTTPException(CoreAPIException):
    """
    API HTTP exception raised when a phone number is not a dictionary.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Phone number must be a dictionary."
