from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.views import EndpointView

from . import definitions


class RolesAPI(EndpointView):
    allowed_methods = ("list",)
    permission_classes = [AllowAny]

    # def get_permissions(self) -> list:
    #     """
    #     Exclude roles endpoint from permission_classes.
    #     Note: You can't use 'self.action' here because it's not set
    #     when calling not accepted method.
    #     """
    #     if "roles" in self.request.path:
    #         retrieve_permission_list = [AllowAny]
    #         return [permission() for permission in retrieve_permission_list]
    #     else:
    #         return super().get_permissions()

    def list(self, request):
        roles = {role[0]: role[1] for role in definitions.ACCOUNT_ROLES if role[0] != definitions.PARENT_SHORT}
        return Response(roles)
