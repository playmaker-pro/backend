from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.base_view import EndpointView

from . import definitions


class RolesAPI(EndpointView):
    allowed_methods = ("list",)
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request: Request) -> Response:
        """
        Return a dictionary of available roles.
        """
        roles = {
            role[0]: role[1]
            for role in definitions.ACCOUNT_ROLES
        }
        return Response(roles)
