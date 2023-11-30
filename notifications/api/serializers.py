from django.urls import reverse
from rest_framework import serializers

from notifications.models import Notification
from notifications.utils import get_notification_redirect_url


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification
    """

    unread_count = serializers.SerializerMethodField()
    redirect_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "redirect_url",
            "notification_type",
            "content",
            "is_read",
            "details",
            "created_at",
            "updated_at",
            "object_id",
            "user",
            "content_type",
            "event_type",
            "unread_count",
        ]

    def get_redirect_url(self, obj: Notification) -> str:
        """
        Constructs a redirect URL for a given notification object.

        This method uses the event type and details of the notification to generate a specific
        redirect URL. The base URL is constructed using the request context.
        """
        request = self.context.get("request")

        # Extract details from obj
        details = obj.details or {}
        # Get the namespaced URL path based on the event type
        namespaced_url_path = reverse(
            get_notification_redirect_url(obj.event_type, details)
        )

        # Construct the full URL by combining scheme, host, and namespaced URL path
        if request:
            scheme = request.scheme
            host = request.get_host()
            return f"{scheme}://{host}{namespaced_url_path}"

        return namespaced_url_path

    def get_unread_count(self, obj: Notification) -> int:
        """
        Retrieves the count of unread notifications from the serializer context.

        This method  add the count of unread notifications to the serialized
        representation of a notification object.
        """
        return self.context.get("unread_count", 0)

    def mark_read(self) -> None:
        """
        Marks the associated notification instance as read.

        This method updates the 'is_read' field of the notification instance
        to True and saves the changes to the database. This method assumes
        that the instance has already been fetched and is available
        as 'self.instance'.
        """
        self.instance.is_read = True
        self.instance.save()
        self.instance.refresh_from_db()
