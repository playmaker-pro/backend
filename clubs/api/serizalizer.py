from clubs.models import Team
from rest_framework import serializers


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj: Team):
        return obj.get_pretty_name()

    class Meta:
        model = Team
        fields = [
            "id",
            "text",
        ]
