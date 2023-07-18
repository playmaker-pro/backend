import logging
import traceback
from typing import Sequence, List, Union

from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from oauthlib.oauth2 import InvalidGrantError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.views import EndpointView
from features.models import FeatureElement, Feature
from users import serializers
from users.errors import (
    FeatureSetsNotFoundException,
    FeatureElementsNotFoundException,
    NoUserCredentialFetchedException,
    GoogleInvalidGrantError,
    ApplicationError,
)
from users.managers import GoogleManager
from users.models import User

# Definicja enpointów nie musi być skoncentrowana tylko i wyłącznie w jedenj klasie.
# jesli poniższe metody będą super-cieńkie (logika będzie poza tymi views)
# to wówczas można już na tym poziomie rozdzielić:
#   AdminUsersAPI  i UsersAPI jeśli byśmy np. chceli podzielic sobie API na to co widzi admin a to co zwykly user
# unikniemy wówczas if... if... i zaszytej logiki
# row-column-permission w samym widoku. Wiadomo jakieś powtorzenia w kodzie są ale przez to że
# logika jest super-thin to nam nie szkodzi.

# Jednak zdaje sobie sprawe ze nie uniknimy sytuacji "if" pod jednm API jak się da to robmy w miare czysto.
from users.serializers import (
    UserRegisterSerializer,
    FeaturesSerializer,
    FeatureElementSerializer,
    GoogleGmailAuthSerializer,
)
from users.services import UserService

user_service: UserService = UserService()
logger = logging.getLogger("django")


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
        if "register" in self.request.path or "google-oauth2" in self.request.path:
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

    @staticmethod
    def feature_sets(request) -> Response:
        """Return all user feature sets."""
        data: List[Feature] = user_service.get_user_features(request.user)
        if not data:
            raise FeatureSetsNotFoundException()
        serializer = FeaturesSerializer(instance=data, many=True)
        return Response(serializer.data)

    @staticmethod
    def feature_elements(request) -> Response:
        """Return all user feature elements."""
        data: List[FeatureElement] = user_service.get_user_feature_elements(
            request.user
        )
        if not data:
            raise FeatureElementsNotFoundException()
        serializer = FeatureElementSerializer(instance=data, many=True)
        return Response(serializer.data)

    @staticmethod
    def google_auth(request):
        """FE -> BE FLOW"""
        google_serializer = GoogleGmailAuthSerializer(data=request.POST)
        google_serializer.is_valid(raise_exception=True)

        validated_data = google_serializer.validated_data
        google_login_flow = GoogleManager()

        try:
            user_info = google_login_flow.get_user_info(
                google_tokens=validated_data.get("token_id")
            )
        except ValueError:
            msg = "Failed to obtain user info from Google."
            logger.error(str(traceback.format_exc()) + f"\n{msg}")
            raise ApplicationError(details=msg)

        user_email = user_info.get("email")
        users: QuerySet = User.objects.filter(email=user_email)
        redirect_path: str = "landing page"

        if users.exists():
            user: User = users.first()
        else:
            redirect_path = "register"
            user: User = user_service.register_from_google(user_info)

            if not user:
                raise NoUserCredentialFetchedException()

        instance, _ = user_service.create_social_account(user=user, data=user_info)
        if not instance:
            raise NoUserCredentialFetchedException()

        refresh: RefreshToken = RefreshToken.for_user(user)
        response = {
            "success": True,
            "redirect": redirect_path,
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

        return Response(response, status=status.HTTP_200_OK)

    @staticmethod
    def google_redirect_url(request):
        # TODO BE flow
        google_login_flow = GoogleManager()

        authorization_url, state = google_login_flow.get_authorization_url()

        # request.session["google_oauth2_state"] = state
        a = redirect(authorization_url)

        return Response({"auth_url": authorization_url})
        # return a

    @staticmethod
    def google_callback(request) -> Union[HttpResponseRedirect, Response]:
        """Google OAuth2 callback endpoint. BE FLOW"""

        input_serializer = GoogleGmailAuthSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        # error = validated_data.get("error")
        state = validated_data.get("state")
        #
        # if error is not None:
        #     return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        #
        # if code is None or state is None:
        #     return Response(
        #         {"error": "Code and state are required."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # session_state = request.session.get("google_oauth2_state")
        # if session_state is None:
        #     return Response(
        #         {"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST
        #     )

        # del request.session["google_oauth2_state"]
        #
        # if state != session_state:
        #     return Response(
        #         {"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST
        #     )

        google_login_flow = GoogleManager()
        try:
            google_tokens = google_login_flow.get_tokens(code=code, state=state)
        except InvalidGrantError:
            raise GoogleInvalidGrantError
        except ValueError:
            raise ApplicationError

        try:
            user_info = google_login_flow.get_user_info(google_tokens=google_tokens)
        except ValueError:
            msg = "Failed to obtain user info from Google."
            logger.error(str(traceback.format_exc()) + f"\n{msg}")
            raise ApplicationError(details=msg)

        user_email = user_info.get("email")
        users: QuerySet = User.objects.filter(email=user_email)
        redirect_path: str = "landing page"

        if users.exists():
            user: User = users.first()
        else:
            redirect_path = "register"
            user: User = user_service.register_from_google(user_info)

            if not user:
                raise NoUserCredentialFetchedException()

        instance, _ = user_service.create_social_account(user=user, data=user_info)
        if not instance:
            raise NoUserCredentialFetchedException()

        refresh: RefreshToken = RefreshToken.for_user(user)
        response = {
            "success": True,
            "redirect": redirect_path,
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

        return Response(response, status=status.HTTP_200_OK)
