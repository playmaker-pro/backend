import typing
from datetime import date, datetime

from rest_framework import serializers

TYPE_TO_SERIALIZER_MAPPING = {
    int: serializers.IntegerField(),
    float: serializers.FloatField(),
    bool: serializers.BooleanField(),
    type(None): serializers.BooleanField(allow_null=True),
    datetime: serializers.DateTimeField(),
    date: serializers.DateField(),
    list: serializers.ListField(),
    dict: serializers.DictField(),
    str: serializers.CharField(),
}

SERIALIZED_VALUE_TYPES = typing.Union[tuple(TYPE_TO_SERIALIZER_MAPPING.keys())]
