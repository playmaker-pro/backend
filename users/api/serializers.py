from datetime import date
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api.serializers import (
    CitySerializer,
    CountrySerializer,
    ProfileEnumChoicesSerializer,
)
from features.models import AccessPermission, Feature, FeatureElement
from premium.api.serializers import (
    PremiumProfileProductSerializer,
    PromoteProfileProductSerializer,
)
from profiles.api.serializers import (
    CoachLicenceSerializer,
    CourseSerializer,
    LanguageSerializer,
)
from profiles.services import ProfileService
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.errors import UserRegisterException
from users.models import Ref, UserPreferences
from users.schemas import LoginSchemaOut
from users.utils.api_utils import modify2custom_exception

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class UserSocialStatsSerializer(serializers.Serializer):
    """User social stats serializer for player profile view"""

    followers = serializers.IntegerField(source="profile.who_follows_me.count")
    following = serializers.IntegerField(source="following.count")
    views = serializers.IntegerField(source="profile.visitation.count_who_visited_me")

    def to_representation(self, instance):
        """
        Convert the instance to a dictionary representation.
        """
        # Call the parent class's to_representation method
        representation = super().to_representation(instance)

        if self.context.get("hide_values", False):
            representation["followers"] = None
            representation["following"] = None
            representation["views"] = None

        return representation


class MainProfileDataSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True, source="declared_role")
    uuid = serializers.SerializerMethodField(
        read_only=True, method_name="my_profile_uuid"
    )
    slug = serializers.CharField(source="profile.slug", read_only=True)
    picture = serializers.CharField(source="picture_url", read_only=True)
    gender = serializers.SerializerMethodField("get_gender")
    has_unread_inquiries = serializers.SerializerMethodField()
    promotion = PromoteProfileProductSerializer(
        read_only=True, source="profile.promotion"
    )
    is_promoted = serializers.BooleanField(read_only=True, source="profile.is_promoted")
    is_premium = serializers.BooleanField(read_only=True, source="profile.is_premium")
    premium_already_tested = serializers.BooleanField(
        read_only=True, source="profile.premium_already_tested"
    )
    premium = PremiumProfileProductSerializer(read_only=True, source="profile.premium")
    social_stats = UserSocialStatsSerializer(read_only=True, source="*")

    class Meta:
        model = User
        fields = (
            "picture",
            "email",
            "first_name",
            "last_name",
            "role",
            "uuid",
            "slug",
            "gender",
            "has_unread_inquiries",
            "promotion",
            "is_promoted",
            "is_premium",
            "premium",
            "premium_already_tested",
            "social_stats",
        )

    def my_profile_uuid(self, instance: User) -> Optional[str]:
        """Return uuid of user's profile if user has declared role, otherwise None"""
        if not instance.declared_role:
            return None
        return instance.profile.uuid

    def get_gender(self, obj: User) -> Optional[dict]:
        """
        Retrieves and serializes the gender information from the user's preferences.

        This method accesses the gender attribute from the user's associated
        UserPreferences model. It then uses the ProfileEnumChoicesSerializer to
        serialize the gender value into a more readable format (e.g., converting
        a gender code to its corresponding descriptive name).
        """
        # Ensure the userpreferences relation exists
        if obj.userpreferences:
            gender_value = obj.userpreferences.gender
            if gender_value is not None:
                # Using ProfileEnumChoicesSerializer for the gender field
                serializer = ProfileEnumChoicesSerializer(
                    source="gender", model=UserPreferences
                )
                return serializer.to_representation(serializer.parse(gender_value))
            return None

    def get_has_unread_inquiries(self, obj: User) -> bool:
        """
        Determines if there are any unread inquiries associated with the user.
        """
        return obj.has_unread_inquiries


class UserPreferencesSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    localization = CitySerializer(required=False, allow_null=True)
    spoken_languages = LanguageSerializer(many=True, required=False, allow_null=True)
    citizenship = CountrySerializer(many=True, required=False, allow_null=True)
    gender = ProfileEnumChoicesSerializer(
        model=UserPreferences, required=False, allow_null=True
    )
    licences = CoachLicenceSerializer(many=True, read_only=True, source="user.licences")
    courses = CourseSerializer(many=True, read_only=True, source="user.courses")

    class Meta:
        model = UserPreferences
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
        }

    def update(self, instance, validated_data):
        spoken_languages = validated_data.get("spoken_languages", None)
        if spoken_languages is not None:  # noqa: 599
            instance.spoken_languages.set(spoken_languages)
            validated_data.pop("spoken_languages")

        instance.save()
        return super().update(instance, validated_data)

    @staticmethod
    def validate_birth_date(value: date) -> date:
        """Check if birthdate is not in the future"""
        now = date.today()
        if value and value > now:
            raise ValidationError(detail="Birth date cannot be in the future")
        return value


class BaseUserDataSerializer(serializers.ModelSerializer):
    picture = serializers.CharField(source="picture_url", read_only=True)
    role = serializers.CharField(read_only=True, source="declared_role")

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "last_login",
            "last_activity",
            "picture",
            "role",
        )
        extra_kwargs = {
            "last_activity": {"read_only": True},
            "last_login": {"read_only": True},
            "id": {"read_only": True},
        }


class UserDataSerializer(BaseUserDataSerializer):
    """User serializer with basic user information"""

    userpreferences = UserPreferencesSerializer(required=False, partial=True)

    class Meta(BaseUserDataSerializer.Meta):
        fields = BaseUserDataSerializer.Meta.fields + ("userpreferences",)
        depth = 1

    def update(self, instance, validated_data) -> User:
        """Override method to achieve nested update"""
        if userpreferences_data := validated_data.pop(  # noqa: E999
            "userpreferences", None
        ):
            userpreferences_data["user"] = instance.pk
            userpreferences_serializer = UserPreferencesSerializer(
                instance.userpreferences, data=userpreferences_data, partial=True
            )
            if userpreferences_serializer.is_valid(raise_exception=True):
                userpreferences_serializer.save()
        return super().update(instance, validated_data)


class UserMainRoleSerializer(serializers.ModelSerializer):
    """Serializer for user main role"""

    class Meta:
        model = User
        fields = ("declared_role",)

    def validate_declared_role(self, value: str) -> str:
        """Check if declared role is in available roles and user has given profile"""
        if value not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise ValidationError(
                detail=f"Declared role must be one of {User.ROLE_CHOICES}"
            )

        model = ProfileService.get_model_by_role(value)
        try:
            model.objects.get(user=self.instance)
        except model.DoesNotExist:
            raise ValidationError(detail=f"User does not have {model.__name__}!")

        return value


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "username"]
        extra_kwargs = {
            "id": {"read_only": True, "required": False},
            "username": {"read_only": True, "required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": True},
        }

    @staticmethod
    def validate_password(value):
        if len(value) < 8:
            raise UserRegisterException(
                fields={"password": "Password must be at least 8 characters long."}
            )
        return value

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)

        return validated_data


class AccessPermissionSerializer(serializers.ModelSerializer):
    """Serializer for access permission."""

    class Meta:
        model = AccessPermission
        fields = ("role", "access")


class FeatureElementSerializer(serializers.ModelSerializer):
    """Serializer for feature element."""

    access_permissions = AccessPermissionSerializer(many=True)

    class Meta:
        model = FeatureElement
        fields = ("name", "permissions", "access_permissions")


class FeaturesSerializer(serializers.ModelSerializer):
    """Serializer for features."""

    elements = FeatureElementSerializer(many=True)

    class Meta:
        model = Feature
        fields = ("name", "keyname", "elements", "enabled")


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)  # Use the function to raise the custom exception
        return validated_data


class CreateNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Check that the new_password and confirm_new_password fields match.
        """
        if data["new_password"] != data["confirm_new_password"]:
            raise UserRegisterException(
                fields={"non_field_errors": "Passwords must match"}
            )
        return data

    def validate_new_password(self, password: str) -> str:
        """
        Validates the new password based on pre-defined criteria.
        """
        if len(password) < 8:
            raise UserRegisterException(
                fields={"password": "Password must be at least 8 characters long."}
            )
        return password

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)

        return validated_data


class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        user: User = self.user
        return LoginSchemaOut(
            id=user.pk,
            first_name=user.first_name,
            last_name=user.last_name,
            **attrs,
        ).dict()


class UserProfilePictureSerializer(serializers.ModelSerializer):
    """Serializer for updating User picture"""

    picture = serializers.ImageField(allow_null=True, write_only=True)

    __allowed_extensions = ["jpeg", "jpg", "png"]

    class Meta:
        model = User
        fields = ("picture",)

    def validate_picture(self, value):
        """Validate the picture size, max up to 2MB."""
        if value:
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("The maximum file size is 2MB.")

            extension = value.name.split(".")[-1].lower()
            if extension not in self.__allowed_extensions:
                raise serializers.ValidationError(
                    f"Allowed formats: {self.__allowed_extensions}"
                )

        return value

    @property
    def data(self):
        return UserDataSerializer(self.instance).data


class RefSerializer(serializers.ModelSerializer):
    referral_code = serializers.UUIDField(read_only=True, source="uuid")
    invited_users = serializers.SerializerMethodField()

    class Meta:
        model = Ref
        fields = ("referral_code", "invited_users")

    def get_invited_users(self, obj):
        return obj.registered_users.count()
