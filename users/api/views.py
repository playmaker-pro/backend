import logging
import traceback
import typing

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.custom_throttling import DefaultThrottle, EmailCheckerThrottle
from api.views import EndpointView
from features.models import Feature, FeatureElement
from notifications.services import NotificationService
from users.api.serializers import (
    CreateNewPasswordSerializer,
    CustomTokenObtainSerializer,
    FeatureElementSerializer,
    FeaturesSerializer,
    MainProfileDataSerializer,
    RefSerializer,
    ResetPasswordSerializer,
    UserProfilePictureSerializer,
    UserRegisterSerializer,
)
from users.errors import (
    ApplicationError,
    EmailNotAvailable,
    EmailNotValid,
    InvalidTokenException,
    InvalidUIDException,
    InvalidUIDServiceException,
    NoSocialTokenSent,
    NoUserCredentialFetchedException,
    SocialAccountInstanceNotCreatedException,
    UserEmailNotValidException,
)
from users.managers import FacebookManager, GoogleManager, UserTokenManager
from users.models import Ref, User, UserRef
from users.schemas import (
    RedirectAfterGoogleLogin,
    UserFacebookDetailPydantic,
    UserGoogleDetailPydantic,
)
from users.services import PasswordResetService, UserService
from users.tasks import track_user_login_task

user_service: UserService = UserService()
password_reset_service: PasswordResetService = PasswordResetService()

logger = logging.getLogger(__name__)


class UserRegisterEndpointView(EndpointView):
    permission_classes = [AllowAny]
    throttle_classes = [EmailCheckerThrottle]

    @staticmethod
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

        if referral_code := request.data.get("referral_code"):
            try:
                ref = Ref.objects.get(uuid=referral_code)
                UserRef.objects.create(user=user, ref_by=ref)
            except Ref.DoesNotExist:
                pass

        return Response(serialized_data)

    def verify_email(self, request: Request, uidb64: str, token: str) -> Response:
        """
        Verifies a user's email address using a token and user ID (uidb64)
        passed in the request.

        This method is designed to handle a GET request containing an uidb64
        and token as query parameters.

        It validates these parameters to ensure they correspond to a valid user
        and that the token is legitimate. If validation is successful, the user's
        'is_email_verified' field is set to True.
        """

        try:
            user = UserService.get_user_from_uid(uidb64)
        except InvalidUIDServiceException:
            raise InvalidUIDException

        if not UserTokenManager.is_token_valid(user, token):
            raise InvalidTokenException

        UserService.change_email_verify_flag(user)
        response = {
            "id": user.pk,
            "success": True,
            **user_service.create_tokens(user),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        return Response(response)


class UsersAPI(EndpointView):
    permission_classes = (IsAuthenticated,)
    allowed_methods = ("list", "post", "put", "update")

    def get_permissions(self) -> typing.Sequence:
        """
        Exclude register endpoint from permission_classes.
        Note: You can't use 'self.action' here because it's not set
        when calling not accepted method.
        """
        if (
            "google-oauth2" in self.request.path
            or "facebook-oauth2" in self.request.path
        ):
            retrieve_permission_list = [AllowAny]
            return [permission() for permission in retrieve_permission_list]
        else:
            return super().get_permissions()

    def my_main_profile(self, request: Request) -> Response:
        """
        Returns user's main profile data {role, uuid} based on `declared_role`.
        """
        serializer = MainProfileDataSerializer(instance=request.user)
        return Response(serializer.data)

    @staticmethod
    def feature_sets(request) -> Response:
        """Returns all user feature sets."""
        data: typing.List[Feature] = user_service.get_user_features(request.user)
        serializer = FeaturesSerializer(instance=data, many=True)
        if not data:
            return Response(status=status.HTTP_204_NO_CONTENT, data=serializer.data)
        return Response(serializer.data)

    @staticmethod
    def feature_elements(request) -> Response:
        """Returns all user feature elements."""
        data: typing.List[FeatureElement] = user_service.get_user_feature_elements(
            request.user
        )
        serializer = FeatureElementSerializer(instance=data, many=True)
        if not data:
            return Response(status=status.HTTP_204_NO_CONTENT, data=serializer.data)
        return Response(serializer.data)

    @staticmethod
    def _social_media_auth(
        manager: typing.Union[GoogleManager, FacebookManager], provider: str
    ) -> dict:
        """
        Authenticate a user via social media and perform necessary actions based on the user's status.

        This static method is responsible for authenticating a user through a specified social media provider,
        such as Google or Facebook, using the provided manager. Depending on the user's status and information,
        it performs actions like retrieving user details, registering new users, and creating associated social
        media accounts. The method returns a response dictionary indicating the success of the authentication
        process and additional information.

        Args:
            manager (Union[GoogleManager, FacebookManager]): An instance of the social media manager responsible
                for handling authentication and user information retrieval.
            provider (str): The name of the social media provider (e.g., "Google" or "Facebook").

        Returns:
            dict: A dictionary containing the result of the authentication process and relevant information.
                  The dictionary includes the following keys:
                  - "success": A boolean indicating whether the authentication was successful.
                  - "redirect": A string representing the path to redirect the user after authentication.
                  - Other key-value pairs related to user tokens and authentication status.

        Raises:
            ApplicationError: If an application-level error occurs during the authentication process.
            UserEmailNotValidException: If the user's email is not valid.
            SocialAccountInstanceNotCreatedException: If the creation of the associated social account fails.

        """  # noqa: E501
        try:
            user_info: typing.Union[
                UserGoogleDetailPydantic, UserFacebookDetailPydantic
            ]
            user_info = manager.get_user_info()
        except ValueError as e:
            logger.exception(str(traceback.format_exc()) + f"\n{str(e)}")
            raise ApplicationError(details=str(e))

        user_email: str = user_info.email
        user: typing.Optional[User] = user_service.filter(email=user_email)

        redirect_path: str = RedirectAfterGoogleLogin.LANDING_PAGE.value

        if not user:
            redirect_path = RedirectAfterGoogleLogin.REGISTER.value
            user: User = user_service.register_from_social(user_info)

            if not user:
                raise UserEmailNotValidException()

        instance, _ = user_service.create_social_account(
            user=user, data=user_info, provider=provider
        )
        if not instance:
            raise SocialAccountInstanceNotCreatedException()

        response = {
            "id": user.pk,
            "success": True,
            "redirect": redirect_path,
            **user_service.create_tokens(user),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        if not getattr(settings, "DISABLE_EXTERNAL_TASKS", False):
            track_user_login_task.delay(user.pk)

        return response

    def google_auth(self, request):
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
            raise NoSocialTokenSent()
        google_manager: GoogleManager = GoogleManager(token_id)

        try:
            response = self._social_media_auth(google_manager, "Google")
        except UserEmailNotValidException:
            raise NoUserCredentialFetchedException(details="User email not valid")
        except SocialAccountInstanceNotCreatedException:
            raise NoUserCredentialFetchedException(
                details="No user data fetched from Google or data is not valid. Please try again."  # noqa
            )
        except Exception as e:
            raise ValidationError from e

        return Response(response, status=status.HTTP_200_OK)

    def facebook_auth(self, request):
        token_id = request.data.get("token_id")
        if not token_id:
            raise NoSocialTokenSent()
        facebook_manager: FacebookManager = FacebookManager(token_id)

        try:
            response = self._social_media_auth(facebook_manager, "Facebook")
        except UserEmailNotValidException:
            raise NoUserCredentialFetchedException(details="User email not valid")
        except SocialAccountInstanceNotCreatedException:
            raise NoUserCredentialFetchedException(details="User instance not created")
        except Exception as e:
            raise ValidationError from e

        return Response(response)


class UserManagementAPI(EndpointView):
    http_method_names = ["post"]
    throttle_classes = [DefaultThrottle]

    def update_profile_picture(self, request: Request) -> Response:
        """
        Update user profile picture.
        """
        serializer = UserProfilePictureSerializer(
            instance=request.user, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    serializer_class = CustomTokenObtainSerializer

    def post(self, request: Request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.is_email_verified
            and request.user.profile
            and (meta := request.user.profile.meta)
        ):
            NotificationService(meta).notify_confirm_email()
        return super().post(request, *args, **kwargs)


class RefreshTokenCustom(TokenRefreshView):
    """
    Returns an access and refresh JWT pair using an existing refresh token.
    Returns status codes 401 and 400 if the refresh token is expired or invalid, respectively.
    """  # noqa: E501

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class EmailAvailability(EndpointView):
    """
    Checks if the email is available for registration.
    """

    permission_classes = [AllowAny]
    throttle_classes = [EmailCheckerThrottle]

    @staticmethod
    def verify_email(request) -> Response:
        """verify email address, if is already in use"""
        email: str = request.data.get("email")
        try:
            validate_email(email)
        except DjangoValidationError as e:
            raise EmailNotValid(details=e)

        response: bool = user_service.email_available(email)
        if not response:
            raise EmailNotAvailable()

        return Response(
            {"success": True, "email_available": response}, status=status.HTTP_200_OK
        )


class PasswordManagementAPIView(EndpointView):
    serializer_class = CreateNewPasswordSerializer
    permission_classes = (AllowAny,)

    def reset_password(self, request: Request) -> Response:
        """
        Handle the POST request to initiate the password reset process.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(
            raise_exception=True
        )  # This will now handle email validation and raise custom exceptions
        email = serializer.validated_data.get("email")
        user = password_reset_service.get_user_by_email(email)

        if user:
            reset_url = UserTokenManager.create_url(user)
            password_reset_service.send_reset_email(user, reset_url)

        return Response(
            {
                "detail": "If an account with the provided email exists, "
                "you'll receive further instructions."
            },
            status=status.HTTP_200_OK,
        )

    def create_new_password(
        self, request: Request, uidb64: str, token: str
    ) -> Response:
        """
        Process the request to reset a user's password using a token.
        """
        # Use the serializer for validation.
        serializer = CreateNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.get_user_from_uid(uidb64)
        except InvalidUIDServiceException:
            raise InvalidUIDException

        if UserTokenManager.is_token_valid(user, token):
            # Reset the user's password
            password_reset_service.reset_user_password(
                user, serializer.validated_data["new_password"]
            )

            return Response(
                {
                    "success": True,
                    "detail": "Password reset successful",
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )

        raise InvalidTokenException


class UserRefAPIView(EndpointView):
    def get_my_data(self, request: Request) -> Response:
        """
        Get user referral information.
        """
        try:
            ref_obj = Ref.objects.get(user=request.user)
        except Ref.DoesNotExist:
            return Response(
                {"detail": "Referral code not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = RefSerializer(ref_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
