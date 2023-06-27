from api.errors import CoreAPIException
from rest_framework import status


class VerificationCompletionFieldsWrongSetup(Exception):
    pass


class InvalidUser(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Request has not defined user or it is incorrect."


class UserAlreadyHasProfile(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Unable to create profile for given user. User already has a profile."
    )


class InvalidUserRole(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Request has not defined user role or it is incorrect."
