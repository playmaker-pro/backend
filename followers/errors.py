from rest_framework import status

from api.errors import CoreAPIException


class FollowDoesNotExist(CoreAPIException):
    """
    Raised when a Follow entity is not found in the system.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given Follow does not exist"


class FollowNotFoundServiceException(Exception):
    """
    Raised by service-level methods when a Follow is not found.
    """

    pass


class SelfFollowServiceException(Exception):
    """Raised by service-level methods when a user attempts to follow their own profile."""

    pass


class SelfFollowException(CoreAPIException):
    """
    Raised when a user attempts to follow their own profile.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You cannot follow your own profile"


class AlreadyFollowingServiceException(Exception):
    """Exception raised when a user tries to follow an entity they are already following."""

    pass


class AlreadyFollowingException(CoreAPIException):
    """
    Raised when a user attempts to follow an entity they are already following.
    """

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, entity_type="entity"):
        self.detail = f"You are already following this {entity_type}."
