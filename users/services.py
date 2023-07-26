from typing import Dict, List, Optional, Set, Tuple

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from rest_framework_simplejwt.tokens import RefreshToken

from api.schemas import RegisterSchema
from features.models import AccessPermission, Feature, FeatureElement
from profiles.models import PROFILE_TYPE
from users.entities import UserGoogleDetailPydantic

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

    def user_has_profile(self, user: User, profile: PROFILE_TYPE) -> bool:
        """Check if given user already has profile on given type"""
        try:
            return profile.objects.get(user=user)
        except profile.DoesNotExist:
            return False

    @staticmethod
    def register(data: dict) -> User:
        """Save User instance with given data."""

        user_schema: RegisterSchema = RegisterSchema(**data)
        user: User = User(**user_schema.user_creation_data())

        user.declared_role = None
        user.state = User.STATE_NEW
        user.username = user.email
        user.set_password(user_schema.password)

        user.save()
        return user

    @staticmethod
    def access_permission_filtered_by_user_role(**kwargs) -> Set[int]:
        #  TODO Access permission is a "Mock", because there is no Role model in user application.
        #   If model will be created, we should get role from request: requests.user.role
        #   In addition, AccessPermission model has and attribute called role (not a table field),
        #   that's why we can't filter by this name.
        #   access_permissions_ids = {
        #   obj.id for obj in AccessPermission.objects.filter(role__id=kwargs.get('role_id'))
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
    def register_from_google(data: UserGoogleDetailPydantic) -> Optional[User]:
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
        user: User, data: UserGoogleDetailPydantic
    ) -> Tuple[Optional[SocialAccount], Optional[bool]]:
        """Check if user has social account, if not create one."""

        if not isinstance(data, UserGoogleDetailPydantic):
            return None, None

        result: SocialAccount = SocialAccount.objects.filter(user=user).first()
        response: SocialAccount = result
        created: bool

        if not result:
            if not data:
                return None, None

            response = SocialAccount.objects.create(
                user=user, provider="google", uid=data.sub, extra_data=data.dict()
            )
            created = True
        else:
            created = False

        return response, created
