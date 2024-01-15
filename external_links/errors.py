from rest_framework import status

from api.errors import CoreAPIException


class LinkSourceNotFoundServiceException(Exception):
    def __init__(self, source_name):
        self.source_name = source_name
        super().__init__(self, f"Link source '{self.source_name}' not found.")


class LinkSourceNotFound(CoreAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Provided link source not found"

    def __init__(self, source_name):
        self.source_name = source_name
        detail = f"Provided link source '{self.source_name}' not found."
        super().__init__(details=detail)
