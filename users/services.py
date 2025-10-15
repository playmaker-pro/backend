import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlparse

from allauth.socialaccount.models import SocialAccount
from cities_light.models import City
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.utils.encoding import DjangoUnicodeDecodeError, force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken

from features.models import AccessPermission, Feature, FeatureElement
from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from mailing.utils import build_email_context
from premium.models import PremiumType
from users.errors import CityDoesNotExistException, InvalidUIDServiceException
from users.managers import UserTokenManager
from users.models import UserPreferences
from users.schemas import (
    RegisterSchema,
    UserFacebookDetailPydantic,
    UserGoogleDetailPydantic,
)

if TYPE_CHECKING:
    from profiles.models import PROFILE_TYPE

User = get_user_model()


class UserService:
    """User service class for handling user operations"""

    def get_user(self, user_id: int) -> Optional[User]:
        """return User or None if it doesn't exist"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return

    @staticmethod
    def filter(**kwargs) -> Optional[User]:
        try:
            user = User.objects.get(**kwargs)
            return user
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def create_tokens(user: User) -> Dict[str, str]:
        """Create tokens for given user"""
        tokens: RefreshToken = RefreshToken.for_user(user)
        return {
            "refresh_token": str(tokens),
            "access_token": str(tokens.access_token),
        }

    def set_role(self, user: User, role: str) -> None:
        """Set role to user"""
        user.set_role(role)

    def user_has_profile(self, user: User, profile: "PROFILE_TYPE") -> bool:
        """Check if given user already has profile on given type"""
        try:
            return profile.objects.get(user=user)
        except profile.DoesNotExist:
            return False

    @staticmethod
    def register(data: dict) -> User:
        """Save User instance with given data."""

        user_schema: RegisterSchema = RegisterSchema(**data)
        user: User = User(**user_schema.dict())

        user.declared_role = None
        user.state = User.STATE_NEW
        user.set_password(user_schema.password)

        user.save()
        return user

    @staticmethod
    def access_permission_filtered_by_user_role(**kwargs) -> Set[int]:
        #  TODO Access permission is a "Mock", because there is no Role model in
        #   user application. If model will be created, we should get role from
        #   request: requests.user.role. In addition, AccessPermission model has and
        #   attribute called role (not a table field), that's why we can't filter by
        #   this name.
        #   access_permissions_ids = {
        #   obj.id for obj in AccessPermission.objects.filter(
        #   role__id=kwargs.get('role_id')
        #   )
        #   }

        access_permissions_ids: Set[int] = {
            obj.id for obj in AccessPermission.objects.all()
        }
        return access_permissions_ids

    def get_user_features(self, user: User) -> List[Feature]:
        """Returns user features by his role"""
        # map_roles = {key: val for key, val in ACCOUNT_ROLES}
        # user_role: str = map_roles.get(user.declared_role)

        access_permissions_ids: Set[int] = self.access_permission_filtered_by_user_role(
            role_id=user.declared_role
        )
        feature_elements_ids: Set[int] = {
            obj.id
            for obj in FeatureElement.objects.filter(
                access_permissions__in=access_permissions_ids
            )
        }
        features: List[Feature] = [
            obj for obj in Feature.objects.filter(elements__in=feature_elements_ids)
        ]

        return features

    def get_user_feature_elements(self, user: User) -> List[FeatureElement]:
        """Returns user feature elements"""

        access_permissions_ids: Set[int] = self.access_permission_filtered_by_user_role(
            role_id=user.declared_role
        )

        return [
            obj
            for obj in FeatureElement.objects.filter(
                access_permissions__in=access_permissions_ids
            )
        ]

    @staticmethod
    def register_from_social(data: UserGoogleDetailPydantic) -> Optional[User]:
        """Save User instance with given data taken from Google."""

        password: str = User.objects.make_random_password()
        user: User = User(
            email=data.email,
            first_name=data.given_name,
            last_name=data.family_name,
        )
        try:
            validate_email(user.email)
        except ValidationError:
            return None

        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def create_social_account(
        user: User,
        data: Union[UserGoogleDetailPydantic, UserFacebookDetailPydantic],
        provider: str,
    ) -> Tuple[Optional[SocialAccount], Optional[bool]]:
        """Check if user has social account, if not create one."""

        if not (
            isinstance(data, UserGoogleDetailPydantic)
            or isinstance(data, UserFacebookDetailPydantic)
        ):
            return None, None

        result: SocialAccount = SocialAccount.objects.filter(user=user).first()
        response: SocialAccount = result
        created: bool

        if not result:
            if not data:
                return None, None

            response = SocialAccount.objects.create(
                user=user, provider=provider, uid=data.sub, extra_data=data.dict()
            )
            created = True
        else:
            created = False

        return response, created

    @staticmethod
    def email_available(email: str) -> bool:
        """Verify if email is available for register"""
        return not User.objects.filter(email=email).exists()

    @staticmethod
    def send_email_to_confirm_new_email_address(
        user: User, new_user: bool = True
    ) -> None:
        """Sends an email to a newly registered user to confirm their email address."""
        verification_url = UserTokenManager.create_email_verification_url(user)

        if new_user:
            template = EmailTemplateRegistry.NEW_USER
        else:
            template = EmailTemplateRegistry.CONFIRM_EMAIL
        context = build_email_context(
            user, url=verification_url, mailing_type=template.mailing_type
        )

        MailingService(template(context=context)).send_mail(user)

    @staticmethod
    def change_email_verify_flag(user: User) -> None:
        """
        Verifies a user's email address.
        """
        user.is_email_verified = True
        user.save()

    @staticmethod
    def get_user_from_uid(uidb64: str) -> User:
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            # Ensure that the decoded user_id only contains digit characters for safety
            if not user_id.isdigit():
                raise ValueError("UID contains non-digit characters.")

            return User.objects.get(pk=user_id)
        except (TypeError, ValueError, DjangoUnicodeDecodeError, ObjectDoesNotExist):
            raise InvalidUIDServiceException


class PasswordResetService:
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Retrieve a User object based on the provided email.
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def send_reset_email(user: User, reset_url: str) -> None:
        """
        Send a password reset email to the user.
        """
        # Log the reset URL for debugging purposes
        query = urlparse(reset_url).query
        params = parse_qs(query)
        uidb64 = params.get("uidb64", [""])[0]
        token = params.get("token", [""])[0]

        logger = logging.getLogger("user_activity")
        logger.debug(
            f"Password reset details for {user.email}: uidb64={uidb64}, token={token}"
        )

        # Actual email sending logic
        verification_url = UserTokenManager.create_email_verification_url(user)
        MailingService(
            EmailTemplateRegistry.PASSWORD_CHANGE(
                context={"url": verification_url, "user": user}
            )
        ).send_mail(user)

    @staticmethod
    def reset_user_password(user: User, new_password: str) -> None:
        """
        Set a new password for a given user and save it.
        """
        if user is not None:
            user.set_password(new_password)
            user.save()


class UserPreferencesService:
    @staticmethod
    def get_city_by_id(loc_id: int):
        try:
            city = City.objects.get(id=loc_id)
            return city
        except City.DoesNotExist:
            raise CityDoesNotExistException

    @staticmethod
    def get_users_with_missing_location() -> User:
        user_ids = UserPreferences.objects.filter(
            localization__isnull=True
        ).values_list("user_id", flat=True)
        return User.objects.filter(id__in=user_ids)


class ReferralRewardService:
    def __init__(self, user: User) -> None:
        self._user = user

    def reward_1_referral(self, referred: User) -> None:
        """
        Reward the user for their first referral.
        """
        # Send email to referrer
        MailingService(
            EmailTemplateRegistry.REFERRAL_REWARD_REFERRER_1(
                context={"referred": referred}
            )
        ).send_mail(self._user)

        # Send welcome gift email to referred user
        MailingService(
            EmailTemplateRegistry.REFERRAL_REWARD_REFERRED(
                context={"referrer": self._user}
            )
        ).send_mail(referred)

    def reward_3_referrals(self) -> None:
        """
        Reward the user for their third referral.
        """
        self._user.profile.setup_premium_profile(
            premium_type=PremiumType.CUSTOM, period=14
        )
        MailingService(
            EmailTemplateRegistry.REFERRAL_REWARD_REFERRER_3(
                context={"referrer": self._user}
            )
        ).send_mail(self._user)

    def reward_5_referrals(self) -> None:
        """
        Reward the user for their fifth referral.
        """
        self._user.profile.setup_premium_profile(premium_type=PremiumType.MONTH)
        MailingService(
            EmailTemplateRegistry.REFERRAL_REWARD_REFERRER_5(
                context={"referrer": self._user}
            )
        ).send_mail(self._user)

    def reward_15_referrals(self) -> None:
        """
        Reward the user for their fifteenth referral.
        """
        self._user.profile.setup_premium_profile(
            premium_type=PremiumType.CUSTOM, period=180
        )
        MailingService(
            EmailTemplateRegistry.REFERRAL_REWARD_REFERRER_15(
                context={"referrer": self._user}
            )
        ).send_mail(self._user)

    def check_and_reward(self) -> None:
        """
        Check the number of referrals and reward the user accordingly.
        """
        registered_users = self._user.ref.registered_users.all()
        invited_users = registered_users.count()

        if invited_users == 1:
            self.reward_1_referral(referred=registered_users.first().user)
        elif invited_users == 3:
            self.reward_3_referrals()
        elif invited_users == 5:
            self.reward_5_referrals()
        elif invited_users == 15:
            self.reward_15_referrals()
