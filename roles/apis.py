from rest_framework.response import Response

from api.views import EndpointView

from . import definitions


class RolesAPI(EndpointView):
    allowed_methods = ("list",)

    def list(self, request):
        roles = {role[0]: role[1] for role in definitions.ACCOUNT_ROLES}
        return Response({"roles": roles})
