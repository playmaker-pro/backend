from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from api.views import EndpointView
from drf_yasg.utils import swagger_auto_schema
from api.swagger_schemas import ROLES_API_SWAGGER_SCHEMA

from . import definitions


class RolesAPI(EndpointView):
    allowed_methods = ("list",)
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(**ROLES_API_SWAGGER_SCHEMA)
    def list(self, request: Request) -> Response:
        """
        Return a dictionary of available roles.
        """
        roles = {
            role[0]: role[1]
            for role in definitions.ACCOUNT_ROLES
            if role[0] != definitions.PARENT_SHORT
        }
        return Response(roles)
