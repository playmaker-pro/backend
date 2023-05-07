import json
import traceback

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class CoreAPIException(APIException):
    fields = None
    pointer = None
    detail = ""
    default_detail = ""

    def __init__(self, details=None, pointer=None):
        super(APIException, self).__init__()
        print(" ------ ")
        print(self.pointer, self.default_detail, self.status_code, self.fields)
        self.pointer = pointer
        if not details:
            self.detail = self.default_detail
        else:
            self.detail = details

        self.__str__()

    def __str__(self):
        data = {
            "success": False,
            "detail": self.detail
            if len(str(self.detail).strip()) > 1
            else self.default_detail,
        }

        if self.fields is not None:
            data["fields"] = self.fields

        # if self.messages is not None:
        #     data['messages'] = self.messages

        if self.pointer is not None:
            data["pointer"] = self.pointer

        return json.dumps(data)


def custom_exception_handler(exc, context) -> exception_handler:
    """
    Log DRF errors to the console. As a default, DRF logs only a caught in code exception to the console.
    We want to log all exceptions (in DEV), so we override the default exception handler.
    Usage: add this to the local.py file in the backend/settings folder:
    REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    'EXCEPTION_HANDLER': "path_to_the_module.custom_exception_handler"
    }
    """

    response = exception_handler(exc, context)
    traceback.print_exc()

    return response
