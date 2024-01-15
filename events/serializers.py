from rest_framework import serializers


class EventMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=300)
    callback = serializers.URLField()
