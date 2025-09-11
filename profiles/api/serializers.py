import typing
from datetime import datetime
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count, QuerySet
from django.db.models.functions import ExtractYear
from django.utils import translation
from django.utils.translation import gettext as _
from django.http import QueryDict
from pydantic import parse_obj_as
from rest_framework import serializers

from api.errors import ChoiceFieldValueErrorException, NotOwnerOfAnObject
from api.i18n import I18nSerializerMixin
from api.serializers import ProfileEnumChoicesSerializer
from api.services import LocaleDataService
from clubs import errors as clubs_errors
from clubs.models import Season, Team
from clubs.services import ClubService
from external_links.serializers import ExternalLinksSerializer
from labels.services import LabelService
from profiles import errors, models, services
from profiles.api import consts
from profiles.api import errors as api_errors
from profiles.services import ProfileVideoService
from roles.definitions import CLUB_ROLES, GUEST_SHORT, PROFILE_TYPE_SHORT_MAP
from users.models import UserPreferences
from users.services import UserService
from utils import translate_to
from utils.factories import utils
from voivodeships.serializers import VoivodeshipSerializer

User = get_user_model()

clubs_service: ClubService = ClubService()
users_service: UserService = UserService()
locale_service: LocaleDataService = LocaleDataService()
label_service: LabelService = LabelService()


class PlayerPositionSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for the player's position, including the ID and name of the position.
    """

    class Meta:
        model = models.PlayerPosition
        fields = ["id", "name", "shortcut", "shortcut_pl"]

    def to_representation(self, instance):
        """Override to return translated position names and appropriate shortcuts."""
        data = super().to_representation(instance)

        # Get the current language from context
        current_language = self.context.get('language', 'pl')
        
        # Translate the position name (Polish names in DB)
        data['name'] = str(_(instance.name))
        
        # Return appropriate shortcut based on language
        if current_language == 'pl':
            data['shortcut'] = instance.shortcut_pl or instance.shortcut
        else:
            data['shortcut'] = instance.shortcut
        
        return data

class PlayerProfilePositionSerializer(serializers.ModelSerializer):
    player_position = PlayerPositionSerializer()

    class Meta:
        model = models.PlayerProfilePosition
        fields = ["player_position", "is_main"]


class ProfileVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(
        source="get_youtube_thumbnail_url", read_only=True
    )
    label = serializers.SerializerMethodField()

    class Meta:
        model = models.ProfileVideo
        fields = "__all__"
        extra_kwargs = {"user": {"required": False}}

    def get_label(self, obj: models.ProfileVideo) -> Optional[dict]:
        """Get label name. If label is not defined, return empty dict"""
        if not obj.label:
            return None
        serializer = ProfileEnumChoicesSerializer(
            model=models.ProfileVideo,
            required=False,
            raise_exception=False,
            source="label",
            data=obj.label,
        )
        try:
            serializer.is_valid(raise_exception=True)
            return serializer.data
        except ChoiceFieldValueErrorException:
            return None

    def __init__(self, *args, **kwargs) -> None:
        """
        Override init to set url as not required if there is defined instance
        (UPDATE METHOD)
        """
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["url"].required = False

    def validate_label(self, label: str) -> str:
        """Validate label field"""
        choices = list(dict(ProfileVideoService.get_labels()).keys())
        if label and label not in choices:
            raise serializers.ValidationError(
                f"Invalid value: {label}. Expected one of: {choices}"
            )
        return label

    def create(self, validated_data: dict) -> models.ProfileVideo:
        """Override create to set user based on requestor"""
        validated_data["user"] = self.context["requestor"]
        return super().create(validated_data)

    def validate_user(self, user: models.User) -> None:
        """Validate that requestor (User, his PlayerProfile) is owner of the Video"""
        if user != self.context.get("requestor"):
            raise NotOwnerOfAnObject

    def delete(self) -> None:
        """
        Method do perform DELETE action on ProfileVideo object, validation included
        """
        self.validate_user(self.instance.user)
        self.instance.delete()

    def update(
        self, instance: models.ProfileVideo, validated_data: dict
    ) -> models.ProfileVideo:
        """
        Method do perform UPDATE action on ProfileVideo object, validation included
        """
        self.validate_user(instance.user)
        return super().update(instance, self.initial_data)


class LicenceTypeSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.LicenceType
        fields = ["id", "name", "key"]

    def get_name(self, obj) -> str:
        """
        Return translated licence name.
        """
        # Use Django's gettext to translate the licence name
        if obj.name:
            return _(obj.name)
        return ""


class CoachLicenceSerializer(serializers.ModelSerializer):
    licence = LicenceTypeSerializer(read_only=True)

    class Meta:
        model = models.CoachLicence
        fields = "__all__"
        extra_kwargs = {
            "licence_id": {"write_only": True},
            "expiry_date": {"required": False},
            "release_date": {"required": False},
            "is_in_progress": {"required": False},
            "owner_id": {"read_only": True},
            "owner": {"read_only": True},
        }

    def validate(self, attrs: dict) -> dict:
        """
        Validate date format,
        unable to use 'validate_expiry_date' cuz attr isn't required
        """

        if expiry_date := attrs.get("expiry_date"):  # noqa: E999
            try:
                datetime.strptime(expiry_date, "%Y-%m-%d")
            except ValueError:
                raise serializers.ValidationError(
                    {"error": "Invalid date format, must be YYYY-MM-DD."}
                )

        if release_year := attrs.get("release_year"):  # noqa: E999
            min_year = 1970
            max_year = datetime.now().year
            if min_year > release_year or release_year > max_year:
                raise serializers.ValidationError(
                    {
                        "error": f"Invalid date format, must be YYYY between "
                        f"{min_year} and {max_year}."
                    }
                )

        return attrs

    def to_internal_value(self, data: dict) -> dict:
        """
        Override method to define profile based on requestor
        (user who sent a request)
        """
        try:
            data["owner"] = self.context["requestor"]
        except KeyError:
            raise ValueError("Requestor is not defined.")

        return data

    def update(
        self, instance: models.CoachLicence, validated_data: dict
    ) -> models.CoachLicence:
        """Override method to update CoachLicence object"""
        if instance.owner != self.context.get("requestor"):
            raise NotOwnerOfAnObject

        try:
            updated_licence = super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"error": "You already have this licence."}
            )
        # Assign labels based on the updated license
        label_service.assign_licence_labels(updated_licence.owner_id)

        return updated_licence

    def create(self, validated_data) -> models.CoachLicence:
        """Override method to create CoachLicence object"""
        try:
            licence_id = validated_data.pop("licence_id")
            validated_data["licence"] = models.LicenceType.objects.get(id=licence_id)
        except KeyError:
            raise serializers.ValidationError({"error": "Licence ID is required."})

        try:
            validated_data["licence"] = models.LicenceType.objects.get(id=licence_id)
        except models.LicenceType.DoesNotExist:
            raise serializers.ValidationError(
                {"error": "Given licence does not exist."}
            )

        try:
            licence_instance = models.CoachLicence.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"error": "You already have this licence."}
            )
        # Assign labels based on the created license
        label_service.assign_licence_labels(licence_instance.owner_id)
        return licence_instance

    def delete(self) -> None:
        """
        Method do perform DELETE action on CoachLicence object,
        owner validation included
        """
        if self.instance.owner != self.context.get("requestor"):
            raise NotOwnerOfAnObject
        user_id = (
            self.instance.owner_id
        )  # Store the user ID before deleting the licence
        self.instance.delete()
        # Update labels after deleting the licence
        label_service.assign_licence_labels(user_id)


class ProfileVisitHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileVisitHistory
        exclude = ("id",)


class LanguageSerializer(serializers.ModelSerializer):
    priority = serializers.SerializerMethodField(
        read_only=True, method_name="define_priority"
    )
    name = serializers.SerializerMethodField(
        method_name="translate_name", read_only=True
    )

    class Meta:
        model = models.Language
        fields = "__all__"

    def to_internal_value(self, data: str) -> typing.Union[models.Language, str]:
        """Override object to get language either by code and id"""
        if isinstance(data, str):
            return models.Language.objects.filter(code=data).first() or data
        return data

    def define_priority(self, obj: models.Language) -> bool:
        """Define language priority"""
        return locale_service.is_prior_language(obj.priority)

    def translate_name(self, obj) -> str:
        """Translate language name"""
        language = self.context.get("language", "pl")

        try:
            locale_service.validate_language_code(language)
        except ValueError as e:
            raise serializers.ValidationError(e)

        name: str = (
            locale_service.get_english_language_name_by_code(obj.code) or obj.name
        )
        return translate_to(language, name).capitalize()


class PlayersGroupByAgeSerializer(serializers.Serializer):
    def to_representation(self, queryset) -> dict:
        """
        Serialize queryset and create dictionary on structure {age: count_of_players}
        return {
            "total": 4532,
            "14": 29,
            "15": 77,
            "16": 130,
            "17": 242,
            "18": 358,
            ...
        }
        """
        current_year: int = datetime.now().year
        data: list = (
            queryset.annotate(
                birth_year=ExtractYear("user__userpreferences__birth_date")
            )
            .values("birth_year")
            .annotate(count=Count("pk"))
            .order_by("-birth_year")
        )
        result = {current_year - res["birth_year"]: res["count"] for res in data}
        result["total"] = queryset.count()
        return result

    def save(self, **kwargs) -> None:
        raise errors.SerializerError(
            f"{self.__class__.__name__} should not be able to save anything!"
        )


class VerificationStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VerificationStage
        exclude = ("id",)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Course
        fields = "__all__"
        extra_kwargs = {
            "name": {"required": False},
            "owner_id": {"read_only": True},
            "owner": {"read_only": True},
        }

    def validate(self, attrs: dict) -> dict:
        """Validate data"""

        if self.instance:
            name = attrs.get("name") or self.instance.name
            release_year = attrs.get("release_year") or self.instance.release_year
        else:
            name = attrs.get("name")
            release_year = attrs.get("release_year")

        if not name:
            raise serializers.ValidationError({"error": "Name is required."})

        if release_year and (1970 > release_year or release_year > datetime.now().year):
            raise serializers.ValidationError(
                {
                    "error": f"Invalid date format, must be YYYY between 1970 "
                    f"and {datetime.now().year}."
                }
            )

        return attrs

    def delete(self) -> None:
        """
        Method do perform DELETE action on Course object,
        owner validation included
        """
        if self.instance.owner != self.context.get("requestor"):
            raise NotOwnerOfAnObject
        self.instance.delete()

    def update(self, instance: models.Course, validated_data: dict) -> models.Course:
        """Override method to update Course object"""
        if instance.owner != self.context.get("requestor"):
            raise NotOwnerOfAnObject

        return super().update(instance, validated_data)


class BaseTeamContributorInputSerializer(serializers.Serializer):
    # Shared fields
    team_parameter = serializers.CharField(required=True)
    league_identifier = serializers.CharField(required=True)
    team_history = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), required=False, many=True
    )
    gender = serializers.IntegerField(required=False)
    is_primary = serializers.BooleanField(required=False)
    country = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the serializer.

        If the initial data contains a 'team_history' key, it marks the
        'team_parameter', 'league_identifier', and 'season' fields as not required.
        This caters to the scenario where if a team_history is provided, the other
        details are derived from it and thus aren't required
        to be passed in separately.
        """
        super().__init__(*args, **kwargs)
        initial_data = kwargs.get("data")

        if initial_data and initial_data.get("team_history"):
            self.fields["team_parameter"].required = False
            self.fields["league_identifier"].required = False

    def validate_team_parameter(self, value: str) -> typing.Union[int, str]:
        """
        Check if the provided value is numeric and convert it to an integer.
        """
        if value.isdigit():
            return int(value)
        return value

    def validate_league_identifier(self, value: str) -> typing.Union[int, str]:
        """
        Check if the provided league identifier is numeric and convert it to an integer.
        """
        if value.isdigit():
            return int(value)
        return value

    def to_internal_value(self, data):
        # Check if 'team_history' is an integer
        if "team_history" in data:
            if isinstance(data["team_history"], int):
                data["team_history"] = [data["team_history"]]
        return super().to_internal_value(data)

    def validate(
        self, data: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        """
        Check specific validation requirements for the provided data.
        """
        validation_errors = {}
        if not self.partial:
            if data.get("team_history"):
                if "team_parameter" in data:
                    del data["team_parameter"]
                if "league_identifier" in data:
                    del data["league_identifier"]
                return data

                # If 'team_history' is not provided, validate other fields
            if not data.get("team_parameter"):
                validation_errors["team_parameter"] = [
                    "This field is required when team_history is not provided."
                ]
            if not data.get("league_identifier"):
                validation_errors["league_identifier"] = [
                    "This field is required when team_history is not provided."
                ]

            # If there's no 'team_history'
            if not data.get("team_history"):
                # Check if the league_identifier is an ID or name
                league_identifier = data.get("league_identifier")

                # If it's a foreign team (determined by league_identifier being a name)
                if not isinstance(league_identifier, int):
                    # Check if country is provided
                    if not data.get("country"):
                        validation_errors[
                            "country"
                        ] = "This field is required for foreign teams."

                    # Check if gender is provided for the foreign team
                    if not data.get("gender"):
                        if "gender" not in validation_errors:
                            validation_errors["gender"] = []
                        validation_errors["gender"].append(
                            "Gender is required for foreign teams."
                        )

                        # Check if team_parameter is an ID (which shouldn't be the
                        # case for foreign teams)
                    if isinstance(data.get("team_parameter"), int):
                        validation_errors["team_parameter"] = [
                            "Foreign teams require a team name, not an ID."
                        ]

                else:
                    # For non-foreign teams where league_identifier is an ID
                    if data.get("country") and data.get("country") != "PL":
                        validation_errors["league_identifier"] = [
                            "Foreign teams require a league name, not an ID.",
                        ]
        else:
            pass

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data


class PlayerProfileTeamContributorInputSerializer(BaseTeamContributorInputSerializer):
    season = serializers.IntegerField(required=True)
    round = serializers.ChoiceField(
        choices=models.TeamContributor.ROUND_CHOICES, required=False
    )
    is_primary_for_round = serializers.BooleanField(required=False)

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the serializer.

        If the initial data contains a 'team_history' key, it marks the
        'season' field as not required.
        """
        super().__init__(*args, **kwargs)
        initial_data = kwargs.get("data")

        if initial_data and initial_data.get("team_history", []):
            self.fields["season"].required = False

    def validate(self, data):
        data = super().validate(data)  # Now this will return the modified data
        validation_errors = {}

        # If 'team_history' is provided, 'season' becomes optional
        if not self.partial:
            if data.get("team_history", []):
                if "season" in data:
                    del data["season"]
            else:
                # If 'team_history' is not provided, validate 'season'
                if not data.get("season"):
                    validation_errors["season"] = [
                        "This field is required when team_history is not provided."
                    ]
        else:
            pass

        # Raise all accumulated errors

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data


class OtherProfilesTeamContributorInputSerializer(BaseTeamContributorInputSerializer):
    start_date = serializers.DateField(
        required=True, help_text="Start date of the contribution."
    )
    end_date = serializers.DateField(
        required=False, help_text="End date of the contribution."
    )
    role = serializers.ChoiceField(
        choices=models.CoachProfile.COACH_ROLE_CHOICES + CLUB_ROLES, required=True
    )
    custom_role = serializers.CharField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the serializer.

        If the profile is Scout, it marks the role field as a not required.
        """
        super().__init__(*args, **kwargs)
        profile_short_type: typing.Optional[str] = self.context.get(
            "profile_short_type"
        )
        if profile_short_type == "S" and self.initial_data:
            self.fields["role"].required = False

    def validate(
        self, data: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        data = super().validate(data)  # this now returns modified data
        validation_errors = {}

        is_primary = data.get(
            "is_primary", self.instance.is_primary if self.instance else None
        )
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Check if end_date is earlier than start_date
        if end_date and start_date and end_date < start_date:
            validation_errors["end_date"] = "End date cannot be before start date."

        # Specific validations for non-player profiles
        if data.get("is_primary") is True and end_date:
            validation_errors[
                "end_date"
            ] = "End date should not be provided if is_primary is True."
        if self.instance:
            # Case where is_primary changes from True to False,
            # and no end_date is provided
            if (
                self.instance.is_primary
                and is_primary is False
                and not data.get("end_date")
            ):
                data["end_date"] = datetime.now().date()

            # Case where is_primary changes from False to True, clear the end_date
            if not self.instance.is_primary and is_primary is True:
                data["end_date"] = None

        role = data.get("role", self.instance.role if self.instance else None)
        # Validate the 'custom_role' field
        if (
            role not in models.TeamContributor.get_other_roles()
            and data.get("custom_role") is not None
        ):
            validation_errors[
                "custom_role"
            ] = "Custom role should not be provided unless the role is 'Other'."

        # Specific logic based on the profile type
        profile_short_type = self.context.get("profile_short_type")
        if profile_short_type and role:
            if profile_short_type == "T" and role not in dict(
                models.CoachProfile.COACH_ROLE_CHOICES
            ):
                validation_errors["role"] = "Invalid role for coach profile."
            elif profile_short_type == "C" and role not in dict(CLUB_ROLES):
                validation_errors["role"] = "Invalid role for club profile."
        # If any errors found, raise them all at once

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data


class PlayerTeamContributorSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    league_name = serializers.SerializerMethodField()
    league_id = serializers.SerializerMethodField()
    season_name = serializers.SerializerMethodField()
    team_id = serializers.SerializerMethodField()

    class Meta:
        model = models.TeamContributor
        fields = (
            "id",
            "team_id",
            "picture_url",
            "team_name",
            "league_name",
            "league_id",
            "season_name",
            "round",
            "is_primary",
            "is_primary_for_round",
        )

    def get_picture_url(self, obj):
        """
        Retrieve the absolute url of the club logo.
        """
        if self.is_anonymous:
            return None
        request = self.context.get("request")
        team_history = obj.team_history.first()
        try:
            url = request.build_absolute_uri(team_history.club.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    @property
    def is_anonymous(self) -> bool:
        """
        Check if the requestor is anonymous.
        """
        return self.context.get("is_anonymous", False)

    def get_team_id(self, obj: models.TeamContributor) -> Optional[int]:
        """Returns team id"""
        if self.is_anonymous:
            return 0
        team_history = obj.team_history.first()
        return team_history.pk if team_history else None

    def get_team_name(self, obj):
        """
        Retrieves the name of the team associated with the first team_history instance.
        """
        if self.is_anonymous:
            return ""
        team_history = obj.team_history.first()
        if team_history:
            return (
                team_history.short_name
                if hasattr(team_history, "short_name")
                and team_history.short_name is not None
                else team_history.name
            )
        return None

    def get_league_name(self, obj):
        """
        Retrieves the name of the league associated with the first
        team_history instance.
        """
        team_history = obj.team_history.first()
        if team_history and team_history.league_history:
            return team_history.league_history.league.name
        return None

    def get_league_id(self, obj):
        """
        Retrieves the id of the league associated with the first team_history instance.
        """
        team_history = obj.team_history.first()
        if team_history and team_history.league_history:
            return team_history.league_history.league.id
        return None

    def get_season_name(self, obj):
        """
        Retrieves the name of the season associated with the
        first team_history instance.
        """
        team_history = obj.team_history.first()
        if (
            team_history
            and team_history.league_history
            and team_history.league_history.season
        ):
            return team_history.league_history.season.name
        return None


class AggregatedTeamContributorSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    league_name = serializers.SerializerMethodField()
    league_id = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = models.TeamContributor
        fields = [
            "id",
            "team_name",
            "picture_url",
            "league_name",
            "league_id",
            "is_primary",
            "role",
            "custom_role",
            "start_date",
            "end_date",
        ]

    @property
    def is_anonymous(self) -> bool:
        """
        Check if the requestor is anonymous.
        """
        return self.context.get("is_anonymous", False)

    def get_team_name(self, obj: models.TeamContributor) -> str:
        """
        Get the team name for a TeamContributor object by prioritizing the short name
        over the full name for each associated team history object.
        """
        if self.is_anonymous:
            return ""
        team_histories = obj.team_history.all()
        preferred_name = ""
        for th in team_histories:
            if hasattr(th, "short_name") and th.short_name:
                preferred_name = th.short_name
                break  # Exit loop as soon as a short name is found
            elif th.name:
                preferred_name = th.name

        return preferred_name

    def get_picture_url(self, obj: models.TeamContributor) -> typing.Optional[str]:
        """
        Retrieve the absolute url of the club logo.
        """
        if self.is_anonymous:
            return None
        request = self.context.get("request")
        team_history = obj.team_history.first()
        try:
            url = request.build_absolute_uri(team_history.club.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    def get_league_name(self, obj: models.TeamContributor) -> str:
        if obj.team_history.all().exists():
            return obj.team_history.last().league_history.league.name
        return ""

    def get_league_id(self, obj: models.TeamContributor) -> typing.Optional[int]:
        """
        Retrieves the name of the league associated with the first
        team_history instance.
        """
        team_history = obj.team_history.first()
        if team_history and team_history.league_history:
            return team_history.league_history.league.id
        return None

    @staticmethod
    def get_role(
        obj: models.TeamContributor,
    ) -> Optional[typing.Dict[str, str]]:
        """
        Gets the role of the team contributor as a dictionary with 'id' and 'name' keys.
        """
        role_choices = dict(models.CoachProfile.COACH_ROLE_CHOICES + CLUB_ROLES)

        # Check if the role code exists in the role_choices
        if obj.role in role_choices:
            # Return the role in the expected format
            return {"id": obj.role, "name": role_choices[obj.role]}
        return None


class ProfileListSerializer(serializers.ListSerializer):
    exclude_fields: tuple = (
        "playermetrics",
        "player_video",
        "meta",
        "history",
    )

    def to_representation(self, data: list) -> list:
        """Override method to exclude fields from data"""
        return self.exclude_fields_from_response(super().to_representation(data))

    def exclude_fields_from_response(self, data: list) -> list:
        """
        Iterate through list objects and remove elements described
        in self.exclude_fields
        """
        for obj in data:
            for key in self.exclude_fields:
                if key in obj.keys():
                    obj.pop(key, None)
        return data


class ProfileSerializer(serializers.Serializer):
    # recursive imports
    from clubs.api.serializers import TeamHistoryBaseProfileSerializer, TeamSerializer
    from users.api.serializers import UserDataSerializer

    class Meta:
        list_serializer_class = ProfileListSerializer

    serialize_fields = ()  # if empty -> serialize all fields
    exclude_fields: tuple = (
        "event_log",
        "verification_id",
        "team_club_league_voivodeship_ver",
        "external_links_id",
        "verification_stage_id",
        "history_id",
        "meta",
        "meta_updated",
        "birth_date",
        "position_alt",
        "position_raw_alt",
        "position_fantasy",
        "mapper_id",
        "country",
        "updated",
    )  # exclude fields from response
    required_fields = ()  # fields required as 'data'

    # sub-serializers
    user = UserDataSerializer(required=False, partial=True)
    team_object = TeamSerializer(read_only=True)
    team_history_object = TeamHistoryBaseProfileSerializer(read_only=True)
    voivodeship_obj = VoivodeshipSerializer(read_only=True)
    history = ProfileVisitHistorySerializer(required=False, partial=True)
    external_links = ExternalLinksSerializer(required=False)
    address = serializers.CharField(required=False)
    verification_stage = VerificationStageSerializer(required=False)
    labels = serializers.SerializerMethodField()

    # fields related with profile (FK to profile)
    player_positions = PlayerProfilePositionSerializer(
        many=True, required=False, read_only=True
    )
    player_video = ProfileVideoSerializer(many=True, read_only=True)
    # playermetrics = PlayerMetricsSerializer(read_only=True)
    licences = CoachLicenceSerializer(many=True, required=False)

    enums = (
        "transfer_status",
        "soccer_goal",
        "formation",
        "formation_alt",
        "prefered_leg",
        "card",
        "training_ready",
        "agent_status",
        "coach_role",
        "club_role",
        "referee_role",
        "licence",
    )

    # meta fields
    player_stats = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField()

    def get_labels(self, obj):
        """Override labels field to return only visible=True labels"""
        labels = ProfileLabelsSerializer(
            obj.labels.filter(visible=True),
            many=True,
            read_only=True,
        )
        return labels.data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.model: models.PROFILE_TYPE = (
                type(self.instance[0])
                if isinstance(self.instance, (QuerySet, list))
                else type(self.instance)
            )
            if hasattr(self.model, "custom_role"):
                self.serialize_fields += ("custom_role",)

    @property
    def data(self) -> dict:
        """return whole serialized object"""
        return self.to_representation()

    def to_representation(
        self, obj: models.PROFILE_TYPE = None, *args, **kwargs
    ) -> dict:
        """serialize each attr of given model into json"""
        from profiles.serializers_detailed.manager_profile_serializers import (
            PhoneNumberField,
        )

        obj = obj or self.instance
        ret = super().to_representation(obj)
        fields: list[str] = self.serialize_fields or obj.__dict__.keys()

        for field_name in fields:
            if field_name.startswith("_"):
                continue

            field_value = getattr(obj, field_name)

            if field_name in self.enums and field_value:
                serializer_field = ProfileEnumChoicesSerializer(
                    required=False,
                    model=self.model,
                    source=field_name,
                )
            else:
                serializer_field: serializers.Field = self.get_serializer_field(
                    field_value
                )
            ret[field_name] = serializer_field.to_representation(field_value)

            if not isinstance(obj, models.PlayerProfile):
                ret.pop("player_stats", None)

        for field_name in self.exclude_fields:
            ret.pop(field_name, None)

        # For the field 'team_history_object', modify its context to
        # include 'profile_uuid'
        if (
            "team_history_object" in ret
            and hasattr(obj, "team_object")
            and obj.team_object
        ):
            team_history_serializer_context = {
                "request": self.context.get("request"),
                "profile_uuid": obj.uuid,
            }

            # Check if there is a primary team contributor for the team history
            primary_contributor = obj.team_object.teamcontributor_set.filter(
                is_primary=True, profile_uuid=obj.uuid
            ).first()

            if primary_contributor:
                team_history_serializer = self.TeamHistoryBaseProfileSerializer(
                    obj.team_object,
                    context=team_history_serializer_context,
                )
                ret["team_history_object"] = team_history_serializer.data
            else:
                ret["team_history_object"] = None
        else:
            ret["team_history_object"] = None

        # Dynamically add 'phone_number' field if 'dial_code' and 'agency_phone'
        # are in the response
        if "dial_code" in ret and "agency_phone" in ret:
            phone_number_field = PhoneNumberField(source="*")
            ret["phone_number"] = phone_number_field.to_representation(obj)

            ret.pop("dial_code", None)
            ret.pop("agency_phone", None)
        return ret

    def get_serializer_field(
        self, field_value: consts.SERIALIZED_VALUE_TYPES
    ) -> serializers.Field:
        """parse serialized fields"""
        return consts.TYPE_TO_SERIALIZER_MAPPING.get(
            type(field_value), serializers.CharField()
        )

    def get_role(self, obj: typing.Union[QuerySet, models.PROFILE_TYPE]) -> str:
        """get role by model"""
        if isinstance(obj, QuerySet):
            obj = obj.first()
        return services.ProfileService.get_role_by_model(type(obj))

    def save(self) -> None:
        """This serializer should not be able to save anything"""
        raise api_errors.SerializerError(
            f"{self.__class__.__name__} should not be able to save anything!"
        )

    def validate_role(self, role: str) -> None:
        """validate user role, raise exception if doesn't suits to the schema"""
        if role not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise api_errors.InvalidProfileRole

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):  # noqa: E999
            if not clubs_service.team_exist(team_id):
                raise clubs_errors.TeamDoesNotExist

    def validate_club(self) -> None:
        """validate club id"""
        if club_id := self.initial_data.get("club_object_id"):
            if not clubs_service.club_exist(club_id):
                raise clubs_errors.ClubDoesNotExist

    def validate_team_history(self) -> None:
        """validate team history id"""
        if team_history_id := self.initial_data.get("team_history_id"):
            if not clubs_service.team_history_exist(team_history_id):
                raise clubs_errors.TeamHistoryDoesNotExist

    def validate_data(self) -> None:
        """validate ids of team, club and team history"""
        self.validate_team()
        self.validate_club()
        self.validate_team_history()

    def initial_validation(self, data: typing.Dict) -> dict:
        """Validate serializer input (data **kw)"""
        for field in self.required_fields:
            if not data or field not in data.keys():
                raise api_errors.IncompleteRequestBody(self.required_fields)
        return data.dict() if isinstance(data, QueryDict) else data

    def get_player_stats(self, obj: models.PROFILE_TYPE) -> dict:
        """
        Get player summary stats on players catalog
        Solution is temporarily mocked, full logic will be delivered soon
        """
        if isinstance(obj, models.PlayerProfile):
            ...  # TODO(bartnyk): create logic for stats based on metrics, preferably
            # in ProfileService

            return {
                "last_goals_count": utils.get_random_int(0, 8),
                "matches": utils.get_random_int(5, 500),
                "avg_minutes": utils.get_random_int(0, 90),
            }  # temp mocked


class CreateProfileSerializer(ProfileSerializer):
    user_id = serializers.IntegerField()
    uuid = serializers.CharField(read_only=True)
    serialize_fields = (
        "user_id",
        "uuid",
        "role",
    )
    required_fields = ("role",)

    def __init__(self, *args, **kwargs) -> None:
        kwargs["data"] = self.initial_validation(kwargs.get("data"))
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data: dict) -> dict:
        """Get user directly from request auth (requestor)"""
        if user := self.context.get("requestor"):
            data["user_id"] = user.pk
            return super().to_internal_value(data)
        else:
            raise serializers.ValidationError(
                {"error": "Unable to define owner of a request."}
            )

    def to_representation(self, *args, **kwargs) -> dict:
        ret = super(ProfileSerializer, self).to_representation(self.instance)
        return {key: ret[key] for key in self.serialize_fields}

    def validate_user(self):
        """Validate user_is was given and user exist"""
        user_obj: User = self.context.get("requestor")

        if users_service.user_has_profile(user_obj, self.model):
            raise api_errors.UserAlreadyHasProfile

    def handle_positions(self, positions_data: list) -> None:
        """Handles the creation of player positions."""
        positions_service = services.PlayerProfilePositionService()
        # Parse the value as a list of PositionData objects
        positions_data = parse_obj_as(
            typing.List[services.PositionData], positions_data
        )
        positions_service.manage_positions(self.instance, positions_data)

    def validate_data(self) -> None:
        """Validate data"""
        role: str = self.initial_data.get("role")
        try:
            self.model: models.PROFILE_TYPE = services.ProfileService.get_model_by_role(
                role
            )
        except ValueError:
            raise api_errors.InvalidProfileRole

        super().validate_data()
        self.validate_user()

        if role == GUEST_SHORT:
            custom_role = self.initial_data.get("custom_role")
            if not custom_role:
                raise serializers.ValidationError(
                    {
                        "custom_role": f"This field is required when role is "
                        f"{GUEST_SHORT} (GuestProfile)."
                    }
                )

    def save(self) -> None:
        """create profile and set role for given user, need to validate data first"""
        self.validate_data()

        role: str = self.initial_data.pop("role")
        positions_data = self.initial_data.pop("player_positions", None)

        self.instance = self.model.objects.create(**self.initial_data)

        if positions_data and isinstance(self.instance, models.PlayerProfile):
            self.handle_positions(positions_data)

        if role == GUEST_SHORT and "custom_role" in self.initial_data:
            self.instance.custom_role = self.initial_data["custom_role"]
            self.instance.save()


class UpdateProfileSerializer(ProfileSerializer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = self.instance.user

    read_only_fields = (
        "user_id",
        "history_id",
        "mapper_id",
        "verification_id",
        "external_links_id",
        "address_id",
    )  # read-only fields, should not be able to update

    def update_fields(self) -> None:
        """Update fields given in payload"""
        if user_data := self.initial_data.pop("user", None):
            self.user = UserDataSerializer(  # type: ignore  # noqa: F821
                instance=self.instance.user,
                data=user_data,
                partial=True,
            )
            if self.user.is_valid(raise_exception=True):
                self.user.save()

        if verification := self.initial_data.pop("verification_stage", None):
            verification_serializer = serializers.VerificationStageSerializer(
                instance=self.instance.verification_stage,
                data=verification,
                partial=True,
            )
            if verification_serializer.is_valid(raise_exception=True):
                verification_serializer.save()

        if history_data := self.initial_data.pop("history", None):  # noqa: E999
            self.history = ProfileVisitHistorySerializer(
                instance=self.instance.history, data=history_data, partial=True
            )
            if self.history.is_valid(raise_exception=True):
                self.history.save()

        for attr, value in self.initial_data.items():
            if attr in self.read_only_fields:
                continue

            if attr == "player_positions":
                player_position_service = services.PlayerProfilePositionService()
                # Parse the value as a list of PositionData objects
                positions_data = parse_obj_as(typing.List[services.PositionData], value)
                player_position_service.manage_positions(self.instance, positions_data)
            elif hasattr(self.instance, attr):
                setattr(self.instance, attr, value)

    def save(self) -> None:
        """If data is valid, update fields and save profile instance"""
        self.validate_data()
        self.update_fields()
        self.instance.save()


class ProfileLabelsSerializer(I18nSerializerMixin, serializers.Serializer):
    label_name = serializers.CharField(
        source="label_definition.label_name", max_length=25
    )
    label_description = serializers.SerializerMethodField()
    season_name = serializers.CharField(max_length=9)
    icon = serializers.CharField(source="label_definition.icon", max_length=200)
    league = serializers.CharField(max_length=255, required=False)
    team = serializers.CharField(max_length=255, required=False)
    season_round = serializers.CharField(max_length=10, required=False)

    def get_label_description(self, obj) -> str:
        """
        Return translated label description.
        """
        if obj.label_definition and obj.label_definition.label_description:
            from labels.translations import translate_label_description

            return translate_label_description(obj.label_definition.label_description)
        return ""


class BaseProfileDataSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    role = serializers.SerializerMethodField()
    verification_stage = VerificationStageSerializer()
    is_main = serializers.SerializerMethodField(method_name="is_main_profile")

    def get_role(self, obj: models.PROFILE_TYPE) -> str:
        """get role by profile model"""
        return services.ProfileService.get_role_by_model(type(obj))

    def is_main_profile(self, obj: models.PROFILE_TYPE) -> bool:
        """Check if given profile is main profile for user"""
        role = self.get_role(obj)
        return role == obj.user.declared_role


class ProfileSearchSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True, source="userpreferences.age")
    gender = serializers.SerializerMethodField("get_gender")
    player_position = PlayerProfilePositionSerializer(
        source="profile.get_main_position", read_only=True
    )
    specific_role = serializers.SerializerMethodField()
    custom_role = serializers.CharField(
        source="profile.profile_based_custom_role", read_only=True
    )
    picture = serializers.CharField(source="picture_url", read_only=True)
    uuid = serializers.UUIDField(source="profile.uuid", read_only=True)
    slug = serializers.CharField(source="profile.slug", read_only=True)

    class Meta:
        model = models.User
        fields = (
            "role",
            "first_name",
            "last_name",
            "team",
            "age",
            "gender",
            "player_position",
            "specific_role",
            "custom_role",
            "picture",
            "uuid",
            "slug",
        )

    def get_team(self, obj: User) -> Optional[str]:
        """
        Retrieve the team for a given profile.

        For PlayerProfile:
        - Checks if the player has a primary association with a team for the current
        season and round.
        - If such an association exists, it returns the team's display name along with
        its top parent league.

        For other profiles:
        - Checks for the primary team association irrespective of season or round.
        - If an association exists, returns the team's display name along with its top
         parent league.

        If neither of the above conditions is satisfied:
        - The function checks if the profile has a directly associated team object
        and returns its display name.

        If no association is found in any of the above conditions, the function
        returns "bez klubu"
        indicating that the profile does not have an associated team.
        """

        # Check if the user has an associated profile
        if not hasattr(obj, "profile") or not obj.profile:
            return None

        current_season = Season.define_current_season()

        team_contrib = models.TeamContributor.objects.filter(
            profile_uuid=obj.profile.uuid,
            is_primary=True,
        ).first()

        if team_contrib:
            if (
                obj.role == "P"
                and team_contrib.team_history.filter(
                    league_history__season__name=current_season
                ).exists()
            ):
                team_history_instance = team_contrib.team_history.all().first()
                if team_history_instance:
                    return team_history_instance.display_team_with_league

            else:
                team_history_instance = team_contrib.team_history.all().first()
                if team_history_instance:
                    return team_history_instance.display_team_with_league

        if hasattr(obj.profile, "team_object") and obj.profile.team_object:
            return obj.profile.team_object.display_team_with_league

        return None

    def get_specific_role(self, obj: User) -> dict:
        """Get specific role for profile (Coach, Club)"""
        if obj.profile:
            if field_name := obj.profile.specific_role_field_name:
                val = getattr(obj.profile, field_name, None)
                if val is not None:
                    serializer = ProfileEnumChoicesSerializer(
                        source=field_name,
                        read_only=True,
                        model=obj.profile.__class__,
                    )
                    return serializer.to_representation(serializer.parse(val))
                return None

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


class SuggestedProfileSerializer(serializers.Serializer):
    # recursive imports

    from clubs.api.serializers import TeamHistoryBaseProfileSerializer
    from profiles.serializers_detailed.player_profile_serializers import (
        PlayerMetricsSerializer,
    )

    uuid = serializers.UUIDField(read_only=True)
    slug = serializers.CharField()
    role = serializers.CharField(read_only=True, source="user.declared_role")
    picture = serializers.CharField(source="user.picture_url", read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    age = serializers.IntegerField(read_only=True, source="user.userpreferences.age")
    gender = serializers.SerializerMethodField("get_gender")
    player_position = PlayerProfilePositionSerializer(
        source="get_main_position", read_only=True
    )
    specific_role = serializers.SerializerMethodField()
    custom_role = serializers.CharField(
        source="profile_based_custom_role", read_only=True
    )
    playermetrics = PlayerMetricsSerializer(read_only=True)
    team_history_object = serializers.SerializerMethodField()
    is_premium = serializers.BooleanField(read_only=True)

    def get_specific_role(self, obj: models.PROFILE_MODELS) -> Optional[dict]:
        """Get specific role for profile (Coach, Club)"""
        if obj:
            if field_name := obj.specific_role_field_name:
                val = getattr(obj, field_name, None)
                if val is None:
                    return None
                serializer = ProfileEnumChoicesSerializer(
                    source=field_name,
                    read_only=True,
                    model=obj.__class__,
                )
                return serializer.to_representation(serializer.parse(val))

    def get_team_history_object(
        self, profile: models.PROFILE_MODELS
    ) -> typing.Optional[dict]:
        """
        Custom method to handle team history serialization.
        """
        if profile.team_object is not None:
            return self.TeamHistoryBaseProfileSerializer(profile.team_object).data
        return None

    def get_gender(self, obj: models.PROFILE_MODELS) -> Optional[dict]:
        """
        Retrieves and serializes the gender information from the user's preferences.

        This method accesses the gender attribute from the user's associated
        UserPreferences model. It then uses the ProfileEnumChoicesSerializer to
        serialize the gender value into a more readable format (e.g., converting
        a gender code to its corresponding descriptive name).
        """
        # Ensure the userpreferences relation exists
        if obj.user.userpreferences:
            gender_value = obj.user.userpreferences.gender
            if gender_value is not None:
                # Using ProfileEnumChoicesSerializer for the gender field
                serializer = ProfileEnumChoicesSerializer(
                    source="gender", model=UserPreferences
                )
                return serializer.to_representation(serializer.parse(gender_value))
            return None


class ProfileVisitorSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    days_ago = serializers.IntegerField()
    visitor = SuggestedProfileSerializer(source="visitor.profile", read_only=True)


class ProfileVisitSummarySerializer(serializers.Serializer):
    this_month_count = serializers.SerializerMethodField()
    this_year_count = serializers.SerializerMethodField()
    visits = ProfileVisitorSerializer(
        many=True, read_only=True, source="meta.who_visited_me"
    )

    def get_this_month_count(self, profile: models.PROFILE_TYPE) -> int:
        return profile.meta.who_visited_me.count()

    def get_this_year_count(self, profile: models.PROFILE_TYPE) -> int:
        return profile.visitation.visitors_count_this_year


class GenericProfileSerializer(I18nSerializerMixin, serializers.Serializer):
    def to_representation(self, instance: models.PROFILE_TYPE) -> dict:
        from profiles.api.managers import SerializersManager

        if isinstance(instance, models.ProfileMeta):
            instance = instance.profile

        serializer = SerializersManager().get_serializer(type(instance).__name__)
        if serializer:
            return serializer(instance, context=self.context).data
        else:
            raise serializers.ValidationError(
                f"No serializer found for {type(instance).__name__}"
            )
