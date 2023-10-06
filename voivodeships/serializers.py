from rest_framework import serializers

from voivodeships.models import Voivodeships


class VoivodeshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voivodeships
        fields = "__all__"
