from clubs.models import Team
from rest_framework import serializers


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj.full_name or obj.name

    class Meta:
        model = Team
        fields = [
            "id",
            "text",
        ]
