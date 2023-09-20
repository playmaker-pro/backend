import typing
from datetime import datetime

from django.db.models import Count
from django.db.models.functions import ExtractYear
from rest_framework import serializers

from api.errors import NotOwnerOfAnObject
from api.serializers import locale_service
from utils import translate_to

from . import errors, models


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


class PlayerVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(
        source="get_youtube_thumbnail_url", read_only=True
    )
    label = ProfileEnumChoicesSerializer(model=models.PlayerVideo, required=False)

    class Meta:
        model = models.PlayerVideo
        fields = "__all__"

    def __init__(self, *args, **kwargs) -> None:
        """Override init to set url as not required if there is defined instance (UPDATE METHOD)"""
        super().__init__(*args, **kwargs)
        self._profile = None
        if self.instance is not None:
            self.fields["url"].required = False

    def validate_player(self, profile: models.PlayerProfile) -> models.PlayerProfile:
        """Validate that requestor (User, his PlayerProfile) is owner of the Video"""
        if profile.user != self.context.get("requestor"):
            raise NotOwnerOfAnObject
        return profile

    def to_internal_value(self, data: dict) -> dict:
        """Override method to define profile based on requestor (user who sent a request)"""
        if user := self.context.get("requestor"):  # noqa: E999
            try:
                profile = user.playerprofile
            except user._meta.model.playerprofile.RelatedObjectDoesNotExist:
                raise serializers.ValidationError(
                    {"error": "You do not have a player profile."}
                )

            data["player"] = self._profile = profile

            return super().to_internal_value(data)
        else:
            raise serializers.ValidationError(
                {"error": "Unable to define owner of a request."}
            )

    @property
    def profile(self) -> dict:
        """Serialize whole profile of a video owner"""
        from .api_serializers import ProfileSerializer  # avoid circular

        return ProfileSerializer(self._profile).data

    def delete(self) -> None:
        """Method do perform DELETE action on PlayerVideo object, validation included"""
        self.validate_player(self.instance.player)
        self._profile = self.instance.player
        self.instance.delete()


class PlayerMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlayerMetrics
        fields = (
            "season",
            "pm_score",
            "season_score"
        )


class LicenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LicenceType
        fields = ["id", "name", "key"]


class CoachLicenceSerializer(serializers.ModelSerializer):
    licence = LicenceTypeSerializer()

    class Meta:
        model = models.CoachLicence
        fields = "__all__"


class ProfileVisitHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileVisitHistory
        fields = "__all__"


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

    def to_internal_value(self, data: dict) -> typing.Union[models.Language, dict]:
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
