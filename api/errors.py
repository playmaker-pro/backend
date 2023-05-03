import json

from rest_framework.exceptions import APIException


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
