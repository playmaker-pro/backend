from rest_framework import serializers


class TestFormSerializer(serializers.Serializer):
    distance = serializers.CharField()
    leagues = serializers.ListField()
    city = serializers.CharField()
    user = serializers.CharField()

    class Meta:
        fields = ['distance', 'leagues', 'city', 'user']
