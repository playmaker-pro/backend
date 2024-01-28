from rest_framework import status

from api.errors import CoreAPIException


class AccessForbiddenException(CoreAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You don't have permission to perform this operation"


class UserAlreadyExists(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User already exists in database with that email address"
    fields = "email"


class InvalidEmailException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid email address"
    fields = "email"


class NoUserCredentialFetchedException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "No user data fetched from Google or data is not valid. " "Please try again."
    )


class GoogleInvalidGrantError(CoreAPIException):
    """
    Invalid grant error from Google.
    This can happen if the user try access to log in via Google, but params in url
    are wrong (out-dated).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "The provided authorization grant (e.g., authorization code, resource "
        "owner credentials) or refresh token is invalid, expired, revoked, does not "
        "match the redirection URI used in the authorization request, or was "
        "issued to another client"
    )


class ApplicationError(CoreAPIException):
    """
    Application error.
    This can happen if the user try access to log in via Google, but api didn't return
    requested data
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Failed to obtain tokens from Google."


class NoSocialTokenSent(CoreAPIException):
    """No Social token sent. Token is required to authenticate user."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid request. No Social token sent."


class EmailNotValid(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Email is not valid"


class EmailNotAvailable(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Email is not available"


class UserRegisterException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Something went wrong. Check fields list for more details."

    def __init__(self, fields: dict):
        self.fields = fields
        super().__init__(details=self.default_detail)


class UserEmailNotValidException(Exception):
    ...


class SocialAccountInstanceNotCreatedException(Exception):
    ...


class CityDoesNotExistException(Exception):
    """Raises when city couldn't be found in DB"""

    ...


class CityDoesNotExistHTTPException(CoreAPIException):
    """API HTTP exception raised when city does not exist in DB"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "City with given id does not exist"


class InvalidUIDException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid User ID provided."


class InvalidUIDServiceException(Exception):
    """Exception raised when the UID in the UserService is invalid."""


class InvalidTokenException(CoreAPIException):
    """API exception raised when a token validation fails."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The provided token is invalid or has expired."


class UserPreferencesDoesNotExistHTTPException(CoreAPIException):
    """API HTTP exception raised when user preferences do not exist in DB"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User preferences for profile do not exist"
