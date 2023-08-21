from rest_framework.exceptions import ValidationError

from users.errors import UserRegisterException


def validate_serialized_email(error: ValidationError) -> None:
    """
    Validate given error and return specific Exceptions.
    Function used in serializers. Basically it's an exception customization
    """

    raise UserRegisterException(fields=error.detail)
