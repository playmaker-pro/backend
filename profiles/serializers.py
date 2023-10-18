import typing
from datetime import datetime

from django.db import IntegrityError
from django.db.models import Count
from django.db.models.functions import ExtractYear
from rest_framework import serializers

from api.errors import NotOwnerOfAnObject
from api.serializers import locale_service
from clubs.models import TeamHistory
from profiles import errors, models
from utils import translate_to


class ChoicesTuple(typing.NamedTuple):
    id: typing.Union[str, int]
    name: str


class ProfileEnumChoicesSerializer(serializers.CharField, serializers.Serializer):
    """Serializer for Profile Enums"""

    def __init__(self, model: typing.Type[models.models.Model] = None, *args, **kwargs):
        self.model: typing.Type[models.models.Model] = model
        super().__init__(*args, **kwargs)

    def parse_dict(
        self, data: (typing.Union[int, str], typing.Union[int, str])
    ) -> dict:
        """Create dictionary from tuple choices"""
        return {str(val[0]): val[1] for val in data}

    def to_representation(self, obj: typing.Union[ChoicesTuple, str]) -> dict:
        """Parse output"""
        parsed_obj = obj
        if not obj:
            return {}
        if not isinstance(obj, ChoicesTuple):
            parsed_obj = self.parse(obj)
        return {"id": parsed_obj.id, "name": parsed_obj.name}

    def parse(self, _id) -> ChoicesTuple:
        """Get choices by model field and parse output"""
        _id = str(_id)
        choices = self.parse_dict(
            getattr(self.model, self.source).__dict__["field"].choices
        )

        if _id not in choices.keys():
            raise serializers.ValidationError(f"Invalid value: {_id}")

        value = choices[_id]
        return ChoicesTuple(_id, value)


class PlayerPositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the player's position, including the ID and name of the position.
    """

    class Meta:
        model = models.PlayerPosition
        fields = ["id", "name", "shortcut"]


class PlayerProfilePositionSerializer(serializers.ModelSerializer):
    player_position = PlayerPositionSerializer()

    class Meta:
        model = models.PlayerProfilePosition
        fields = ["player_position", "is_main"]


class ProfileVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(
        source="get_youtube_thumbnail_url", read_only=True
    )
    label = ProfileEnumChoicesSerializer(model=models.ProfileVideo, required=False)

    class Meta:
        model = models.ProfileVideo
        fields = "__all__"
        extra_kwargs = {"user": {"required": False}}

    def __init__(self, *args, **kwargs) -> None:
        """Override init to set url as not required if there is defined instance (UPDATE METHOD)"""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["url"].required = False

    def create(self, validated_data: dict) -> models.ProfileVideo:
        """Override create to set user based on requestor"""
        validated_data["user"] = self.context["requestor"]
        return super().create(validated_data)

    def validate_user(self, user: models.User) -> None:
        """Validate that requestor (User, his PlayerProfile) is owner of the Video"""
        if user != self.context.get("requestor"):
            raise NotOwnerOfAnObject

    def delete(self) -> None:
        """Method do perform DELETE action on ProfileVideo object, validation included"""
        self.validate_user(self.instance.user)
        self.instance.delete()

    def update(
        self, instance: models.ProfileVideo, validated_data: dict
    ) -> models.ProfileVideo:
        """Method do perform UPDATE action on ProfileVideo object, validation included"""
        self.validate_user(instance.user)
        return super().update(instance, validated_data)


class PlayerMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlayerMetrics
        fields = ("season", "pm_score", "season_score")


class LicenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LicenceType
        fields = ["id", "name", "key"]


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

        if expiry_date := attrs.get("expiry_date"):
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
                        "error": f"Invalid date format, must be YYYY between {min_year} and {max_year}."
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
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"error": "You already have this licence."}
            )

    def create(self, validated_data) -> models.CoachLicence:
        """Override method to create CoachLicence object"""
        try:
            licence_id = validated_data.pop("licence_id")
        except KeyError:
            raise serializers.ValidationError({"error": "Licence ID is required."})

        try:
            validated_data["licence"] = models.LicenceType.objects.get(id=licence_id)
        except models.LicenceType.DoesNotExist:
            raise serializers.ValidationError(
                {"error": "Given licence does not exist."}
            )

        try:
            return models.CoachLicence.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"error": "You already have this licence."}
            )

    def delete(self) -> None:
        """
        Method do perform DELETE action on CoachLicence object,
        owner validation included
        """
        if self.instance.owner != self.context.get("requestor"):
            raise NotOwnerOfAnObject
        self.instance.delete()


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
            return models.Language.objects.filter(code=data).first()
        return data

    def define_priority(self, obj: models.Language) -> bool:
        """Define language priority"""
        return locale_service.is_prior_language(obj.code)

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
                    "error": f"Invalid date format, must be YYYY between 1970 and {datetime.now().year}."
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
        queryset=TeamHistory.objects.all(), required=False, many=True
    )
    gender = serializers.IntegerField(required=False)
    is_primary = serializers.BooleanField(required=False)
    country = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the serializer.

        If the initial data contains a 'team_history' key, it marks the 'team_parameter',
        'league_identifier', and 'season' fields as not required. This caters to the scenario
        where if a team_history is provided, the other details are derived from it and thus
        aren't required to be passed in separately.
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

                    # Check if team_identifier is an ID (which shouldn't be the case for foreign teams)
                if isinstance(data.get("team_parameter"), int):
                    validation_errors["team_identifier"] = [
                        "Foreign teams require a team name, not an ID."
                    ]

            else:
                # For non-foreign teams where league_identifier is an ID
                if data.get("country") and data.get("country") != "PL":
                    validation_errors["league_identifier"] = [
                        "Foreign teams require a league name, not an ID.",
                    ]

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data


class PlayerProfileTeamContributorInputSerializer(BaseTeamContributorInputSerializer):
    season = serializers.IntegerField(required=True)
    round = serializers.ChoiceField(
        choices=models.TeamContributor.ROUND_CHOICES, required=True
    )

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the serializer.

        If the initial data contains a 'team_history' key, it marks the 'season' field as not required.
        """
        super().__init__(*args, **kwargs)
        initial_data = kwargs.get("data")

        if initial_data and initial_data.get("team_history", []):
            self.fields["season"].required = False

    def validate(self, data):
        data = super().validate(data)  # Now this will return the modified data
        validation_errors = {}

        # If 'team_history' is provided, 'season' becomes optional
        if data.get("team_history", []):
            if "season" in data:
                del data["season"]
            print(f"your data {data}")
        else:
            # If 'team_history' is not provided, validate 'season'
            if not data.get("season"):
                validation_errors["season"] = [
                    "This field is required when team_history is not provided."
                ]

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
        choices=models.CoachProfile.COACH_ROLE_CHOICES, required=True
    )

    def validate(
        self, data: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        data = super().validate(data)  # this now returns modified data
        validation_errors = {}

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
        elif data.get("is_primary") is False and not end_date:
            validation_errors[
                "end_date"
            ] = "End date is required when is_primary is not set."

        # If any errors found, raise them all at once

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data


class PlayerTeamContributorSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    league_name = serializers.SerializerMethodField()
    season_name = serializers.SerializerMethodField()

    class Meta:
        model = models.TeamContributor
        fields = (
            "id",
            "picture_url",
            "team_name",
            "league_name",
            "season_name",
            "round",
            "is_primary",
        )

    def get_picture_url(self, obj):
        """
        Retrieve the absolute url of the club logo.
        """
        request = self.context.get("request")
        team_history = obj.team_history.first()
        try:
            url = request.build_absolute_uri(team_history.team.club.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    def get_team_name(self, obj):
        """
        Retrieves the name of the team associated with the first team_history instance.
        """
        team_history = obj.team_history.first()
        return team_history.team.name if team_history else None

    def get_league_name(self, obj):
        """
        Retrieves the name of the league associated with the first team_history instance.
        """
        team_history = obj.team_history.first()
        if team_history and team_history.league_history:
            return team_history.league_history.league.display_league_top_parent
        return None

    def get_season_name(self, obj):
        """
        Retrieves the name of the season associated with the first team_history instance.
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
    end_date_display = serializers.SerializerMethodField()

    class Meta:
        model = models.TeamContributor
        fields = [
            "id",
            "team_name",
            "picture_url",
            "league_name",
            "is_primary",
            "role",
            "start_date",
            "end_date_display",
        ]

    def get_team_name(self, obj):
        team_histories = obj.team_history.all()
        return ", ".join(set(th.team.name for th in team_histories))

    def get_picture_url(self, obj):
        """
        Retrieve the absolute url of the club logo.
        """
        request = self.context.get("request")
        team_history = obj.team_history.first()
        try:
            url = request.build_absolute_uri(team_history.team.club.picture.url)
        except (ValueError, AttributeError):
            return None
        return url

    def get_league_name(self, obj):
        if obj.team_history.all().exists():
            return (
                obj.team_history.last().league_history.league.display_league_top_parent
            )
        return ""

    def get_end_date_display(self, obj):
        return "aktualnie" if obj.is_primary else obj.end_date
