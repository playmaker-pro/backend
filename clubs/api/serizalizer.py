from clubs.models import Team
from rest_framework import serializers


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    text = serializers.CharField(source="name")
    class Meta:
        model = Team
        fields = ['id', 'text',]


class TeamSerializerSerach(serializers.Serializer):
    
    results = TeamSerializer()
    
    