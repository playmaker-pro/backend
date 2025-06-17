from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification

        fields = [
            "id",
            "title",
            "description",
            "updated_at",
            "created_at",
            "seen",
            "href",
            "icon",
            "picture",
            "picture_profile_role",
        ]

    def mark_as_read(self) -> None:
        """
        Mark the notification as read
        """
        self.instance.mark_as_read()
        self.instance.save()
        self.instance.refresh_from_db()
