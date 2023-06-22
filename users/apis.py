from typing import Sequence

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.views import EndpointView
from users import serializers
from users.models import User

# Definicja enpointów nie musi być skoncentrowana tylko i wyłącznie w jedenj klasie.
# jesli poniższe metody będą super-cieńkie (logika będzie poza tymi views)
# to wówczas można już na tym poziomie rozdzielić:
#   AdminUsersAPI  i UsersAPI jeśli byśmy np. chceli podzielic sobie API na to co widzi admin a to co zwykly user
# unikniemy wówczas if... if... i zaszytej logiki
# row-column-permission w samym widoku. Wiadomo jakieś powtorzenia w kodzie są ale przez to że
# logika jest super-thin to nam nie szkodzi.

# Jednak zdaje sobie sprawe ze nie uniknimy sytuacji "if" pod jednm API jak się da to robmy w miare czysto.
from users.serializers import UserRegisterSerializer
from users.services import UserService

user_service = UserService()


class UsersAPI(EndpointView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserSerializer
    allowed_methods = ("list", "post", "put", "update")

    @staticmethod
    def register(request) -> Response:
        """
        Validate given data and send them to service for register user.
        Returns serialized User data.
        """

        user_data: UserRegisterSerializer = UserRegisterSerializer(data=request.data)
        user_data.is_valid(raise_exception=True)
        user: User = user_service.register(user_data.data)
        serialized_data: dict = UserRegisterSerializer(instance=user).data
        serialized_data.pop("password")

        return Response(serialized_data)

    def get_permissions(self) -> Sequence:
        """
        Exclude register endpoint from permission_classes.
        Note: You can't use 'self.action' here because it's not set
        when calling not accepted method.
        """
        if "register" in self.request.path:
            retrieve_permission_list = [AllowAny]
            return [permission() for permission in retrieve_permission_list]
        else:
            return super().get_permissions()

    def list(self, request):
        # if not user_allowed_to_do that _acction(

        # ):
        #     raise AccessForbiddenException()

        # request_specialty_data = self.specialty_request_usecase.list_network_request(
        #     company_id, user_id
        # )
        # return Response(
        #     self.serializer_class(request_specialty_data, many=True).data,
        #     sta
        return Response(
            self.serializer_class(User.objects.all(), many=True).data,
        )

    def get_queryset(self):
        ...
