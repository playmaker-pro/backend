from django.utils.translation import gettext as _
from rest_framework.exceptions import ErrorDetail, ValidationError

from users.errors import UserRegisterException


def modify2custom_exception(error: ValidationError) -> None:
    """
    Validate given error and return specific Exceptions.
    Function used in serializers. Basically it's an exception customization
    """
    if error.detail.get("email"):
        new_response = []
        for element in error.detail["email"]:
            if element.code == "unique":
                new_message = _(
                    "It is not possible to register with this email address"
                )
                new_response.append(ErrorDetail(new_message))
            else:
                new_response.append(element)
        error.detail["email"] = new_response

    raise UserRegisterException(fields=error.detail)
