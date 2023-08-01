from api.errors import CoreAPIException
from rest_framework import status


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


class IncompleteRequestData(CoreAPIException):
    def __init__(self, required_fields: list):
        self.default_detail = (
            f"Incomplete request's body, required fields: {', '.join(required_fields)}"
        )
        super().__init__()

    status_code = status.HTTP_400_BAD_REQUEST
