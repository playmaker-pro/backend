import logging
import traceback
from typing import List, Optional, Sequence

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ImproperlyConfigured
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.swagger_schemas import (
    GOOGLE_AUTH_SWAGGER_SCHEMA,
    USER_FEATURE_ELEMENTS_SWAGGER_SCHEMA,
    USER_FEATURE_SETS_SWAGGER_SCHEMA,
    USER_LOGIN_ENDPOINT_SWAGGER_SCHEMA,
    USER_REFRESH_TOKEN_ENDPOINT_SWAGGER_SCHEMA,
    USER_REGISTER_ENDPOINT_SWAGGER_SCHEMA,
)
from api.views import EndpointView
from features.models import Feature, FeatureElement
from users import serializers
from users.errors import (
    ApplicationError,
    NoGoogleTokenSent,
    NoUserCredentialFetchedException,
    EmailNotValid,
    UserAlreadyExists,
    EmailNotAvailable,
)
from users.managers import GoogleManager
from users.schemas import UserGoogleDetailPydantic, RedirectAfterGoogleLogin
from users.models import User
from users.serializers import (
    FeatureElementSerializer,
    FeaturesSerializer,
    UserRegisterSerializer,
)
from users.services import UserService

# Definicja enpointów nie musi być skoncentrowana tylko i wyłącznie w jedenj klasie.
# jesli poniższe metody będą super-cieńkie (logika będzie poza tymi views)
# to wówczas można już na tym poziomie rozdzielić:
#   AdminUsersAPI  i UsersAPI jeśli byśmy np. chceli podzielic sobie API na to co widzi admin a to co zwykly user
# unikniemy wówczas if... if... i zaszytej logiki
# row-column-permission w samym widoku. Wiadomo jakieś powtorzenia w kodzie są ale przez to że
# logika jest super-thin to nam nie szkodzi.
# Jednak zdaje sobie sprawe ze nie uniknimy sytuacji "if" pod jednm API jak się da to robmy w miare czysto.


user_service: UserService = UserService()
logger = logging.getLogger("django")


class UsersAPI(EndpointView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserSerializer
    allowed_methods = ("list", "post", "put", "update")

    @staticmethod
    @extend_schema(**USER_REGISTER_ENDPOINT_SWAGGER_SCHEMA)
    def register(request) -> Response:
        """
        Validate given data and register user if everything is ok.
        Returns serialized User data or validation errors.
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
        if (
            "register" in self.request.path
            or "google-oauth2" in self.request.path
            or "email-verification" in self.request.path
        ):
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
    @extend_schema(**USER_FEATURE_SETS_SWAGGER_SCHEMA)
    def feature_sets(request) -> Response:
        """Returns all user feature sets."""
        data: List[Feature] = user_service.get_user_features(request.user)
        serializer = FeaturesSerializer(instance=data, many=True)
        if not data:
            return Response(status=status.HTTP_204_NO_CONTENT, data=serializer.data)
        return Response(serializer.data)

    @staticmethod
    @extend_schema(**USER_FEATURE_ELEMENTS_SWAGGER_SCHEMA)
    def feature_elements(request) -> Response:
        """Returns all user feature elements."""
        data: List[FeatureElement] = user_service.get_user_feature_elements(
            request.user
        )
        serializer = FeatureElementSerializer(instance=data, many=True)
        if not data:
            return Response(status=status.HTTP_204_NO_CONTENT, data=serializer.data)
        return Response(serializer.data)

    @staticmethod
    @extend_schema(**GOOGLE_AUTH_SWAGGER_SCHEMA)
    def google_auth(request):
        """
        post:
        Authenticates user with Google and gets his detailed information.

        Method authenticate user with Google by token_id and returns his data.
        If user exists in our database, then login him, otherwise register.
        As a response returns user access and refresh tokens.
        """
        request_data: dict = request.data

        token_id: str = request_data.get("token_id")
        if not token_id:
            raise NoGoogleTokenSent()

        try:
            google_manager: GoogleManager = GoogleManager()
            user_info: UserGoogleDetailPydantic = google_manager.get_user_info(
                access_token=request_data.get("token_id")
            )
        except ValueError as e:
            logger.error(str(traceback.format_exc()) + f"\n{str(e)}")
            raise ApplicationError(details=str(e))
        except ImproperlyConfigured:
            msg = "Failed to obtain Google credentials."
            logger.error(str(traceback.format_exc()) + f"\n{msg}")
            raise ApplicationError(details=msg)

        user_email: str = user_info.email
        user: Optional[User] = user_service.filter(email=user_email)

        redirect_path: str = RedirectAfterGoogleLogin.LANDING_PAGE.value

        if not user:
            redirect_path = RedirectAfterGoogleLogin.REGISTER.value
            user: User = user_service.register_from_google(user_info)

            if not user:
                raise NoUserCredentialFetchedException()

        instance, _ = user_service.create_social_account(user=user, data=user_info)
        if not instance:
            raise NoUserCredentialFetchedException()

        response = {
            "success": True,
            "redirect": redirect_path,
            **user_service.create_tokens(user),
        }

        return Response(response, status=status.HTTP_200_OK)

    @staticmethod
    def verify_email(request) -> Response:
        """verify email address, if is already in use"""
        try:
            validate_email(request.data.get("email"))
        except ValidationError as e:
            raise EmailNotValid(details=e)

        response: bool = user_service.email_available(request.data.get("email"))
        if not response:
            raise EmailNotAvailable()

        return Response(
            {"success": True, "email_available": response}, status=status.HTTP_200_OK
        )


class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    @extend_schema(**USER_LOGIN_ENDPOINT_SWAGGER_SCHEMA)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenCustom(TokenRefreshView):
    """
    Returns an access and refresh JWT pair using an existing refresh token.
    Returns status codes 401 and 400 if the refresh token is expired or invalid, respectively.
    """

    @extend_schema(**USER_REFRESH_TOKEN_ENDPOINT_SWAGGER_SCHEMA)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
