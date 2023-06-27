from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny
from api.views import EndpointView

from . import definitions


class RolesAPI(EndpointView):
    allowed_methods = ("list",)
    authentication_classes = []
    permission_classes = []

    def list(self, request: Request) -> Response:
        """Return a dictionary of available roles."""
        roles = {
            role[0]: role[1]
            for role in definitions.ACCOUNT_ROLES
            if role[0] != definitions.PARENT_SHORT
        }
        return Response(roles)
