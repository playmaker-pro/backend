from rest_framework import serializers
from api.errors import InvalidLanguagesListInput
from utils import translate_to
import typing


class LanguageListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data: list) -> typing.List[dict]:
        """
        Pass languages as list of tuples as:
        [(language_code, language_name), ...]
        Pass language code (ISO 639-1) as context to translate language names
        Available language codes: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

        {
            language - name of language translated in langauge described by context param
            language_locale - name of language translated as native locale language
            code - language code
        }
        """
        language: str = self.context.get("language", "pl")
        self.validate_input(data)
        return [
            {
                "language": translate_to(language, language_name),
                "language_locale": translate_to(language_code, language_name),
                "code": language_code,
            }
            for language_code, language_name in data
        ]

    def validate_input(self, data: list) -> None:
        """Validate input structure, expect: [(code, name), ...]"""
        if (
            not isinstance(data, list)
            or len(data) == 0
            or not isinstance(data[0], tuple)
        ):
            raise InvalidLanguagesListInput


class LanguageSerializer(serializers.Serializer):
    language = serializers.CharField(read_only=True)
    language_locale = serializers.CharField(read_only=True)
    code = (
        serializers.CharField()
    )  # we assume that UserPreferences will save language by code

    class Meta:
        list_serializer_class = LanguageListSerializer
