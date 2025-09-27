from rest_framework import serializers

from mailing.models import MailingPreferences


class MailingPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingPreferences
        fields = ["system", "marketing"]
