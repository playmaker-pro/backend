"""Notifications API views."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from api.views import EndpointView
from notifications.api.serializers import NotificationSerializer
from notifications.models import Notification



class NotificationsView(EndpointView):
    def get_notifications(self, request: Request) -> Response:
        """
        Get notifications for a user.
        """
        if request.query_params.get("unseen", None) == "true":
            notifications = request.user.profile.meta.notifications.filter(seen=False)
        else:
            notifications = request.user.profile.meta.notifications.all()
        serializer = NotificationSerializer(
            notifications.order_by("-created_at"),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(
            data=serializer.data,
            status=200,
        )

    def mark_as_read(self, request: Request, notification_id: int) -> Response:
        """
        Mark notification as read.
        """
        try:
            notification = request.user.profile.meta.notifications.get(
                id=notification_id
            )
        except Notification.DoesNotExist:
            raise NotFound("Notification with this ID does not exist.")

        if notification.target != request.user.profile.meta:
            raise PermissionDenied(
                "You do not have permission to mark this notification as read."
            )

        serializer = NotificationSerializer(
            notification, context=self.get_serializer_context()
        )
        serializer.mark_as_read()
        return Response(
            data=serializer.data,
            status=200,
        )
