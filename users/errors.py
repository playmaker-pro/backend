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


class FeatureSetsNotFoundException(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Feature sets for user not found"


class FeatureElementsNotFoundException(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Feature elements for user not found"


class NoUserCredentialFetchedException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "No user data fetched from Google or data is not valid. " "Please try again."
    )


class GoogleInvalidGrantError(CoreAPIException):
    """
    Invalid grant error from Google.
    This can happen if the user try access to log in via Google, but params in url are wrong (out-dated).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "The provided authorization grant (e.g., authorization code, resource owner credentials) "
        "or refresh token is invalid, expired, revoked, does not match the redirection "
        "URI used in the authorization request, or was issued to another client"
    )


class ApplicationError(CoreAPIException):
    """
    Application error.
    This can happen if the user try access to log in via Google, but api didn't return requested data
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Failed to obtain tokens from Google."
