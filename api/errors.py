import json
import traceback
from typing import Dict, List, Union

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class CoreAPIException(APIException):
    fields: Union[List[str], dict] = None
    pointer = None
    detail = ""
    default_detail = ""
    field: str = None

    def __init__(self, details=None, pointer=None):
        super(APIException, self).__init__()
        self.pointer = pointer
        if not details:
            self.detail = self.default_detail
        else:
            self.detail = details

        super().__init__(self._prepare_content())

    def _prepare_content(self) -> Dict:
        """Prepare content for the API response."""
        data = {
            "success": False,
            "detail": self.detail
            if len(str(self.detail).strip()) > 1
            else self.default_detail,
        }

        if self.fields is not None:
            data["fields"] = self.fields

        if self.field is not None:
            data["field"] = self.field

        if self.pointer is not None:
            data["pointer"] = self.pointer

        return data

    def __str__(self) -> str:
        """Prepare string representation of the exception."""
        return json.dumps(self._prepare_content())


class InvalidLanguageCode(CoreAPIException):
    """Exception if request received unknown language code to translate with"""

    status_code = status.HTTP_400_BAD_REQUEST


class InvalidAPIRequestParam(CoreAPIException):
    """Exception if request received invalid param"""

    status_code = status.HTTP_400_BAD_REQUEST


class InvalidCountryCode(CoreAPIException):
    """Exception if request received invalid country code"""

    status_code = status.HTTP_400_BAD_REQUEST


class ParamsRequired(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, params_required: list, *args, **kwargs) -> None:
        kwargs["details"] = f"Params required: {', '.join(params_required)}"
        super().__init__(*args, **kwargs)


class ObjectDoesNotExist(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Given object does not exists."


class NotOwnerOfAnObject(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You are not allowed to modify this object."


def custom_exception_handler(exc, context) -> exception_handler:
    """
    Log DRF errors to the console.
    As a default, DRF logs only a caught in code exception to the console.
    We want to log all exceptions (in DEV), so we override the default exception handler.
    Usage: add this to the local.py file in the backend/settings folder:
    REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    'EXCEPTION_HANDLER': "path_to_the_module.custom_exception_handler"
    }
    """  # noqa: E501

    response = exception_handler(exc, context)
    traceback.print_exc()

    return response
