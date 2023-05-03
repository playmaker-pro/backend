from rest_framework import status

from api.errors import CoreAPIException


# To tylko przykład
class AccessForbiddenException(CoreAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You don't have permission to perform this operation"
