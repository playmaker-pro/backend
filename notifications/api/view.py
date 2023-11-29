import typing
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from rest_framework import authentication, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.views import EndpointView
from notifications.api.serializers import NotificationSerializer
from notifications.models import Notification
from notifications.services import NotificationService
from profiles.api import errors as api_errors
from profiles.services import ProfileService

profile_service = ProfileService()
notification_service = NotificationService()


class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)


class UserNotificationView(EndpointView):
    permission_classes = (IsAuthenticated,)

    def get_paginated_queryset(
        self, qs: QuerySet = None
    ) -> typing.Optional[typing.List[Notification]]:
        """Paginate queryset with custom page size"""
        self.pagination_class.page_size = 20
        return super().get_paginated_queryset(qs)

    def get_notifications(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        """
        Retrieves a paginated list of notifications for a given user profile.

        This method fetches notifications associated with the specified profile UUID. It supports
        filtering for only the latest notifications based on a query parameter. The response includes
        serialized notification data.
        """
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist()

        if request.user != profile.user:
            raise PermissionDenied

        latest_only = request.query_params.get("latest_only") == "true"

        # Unpack the tuple to get notifications and unread count
        (
            combined_notifications,
            unread_count,
        ) = notification_service.get_combined_notifications(
            user=request.user, profile_uuid=profile_uuid, latest_only=latest_only
        )

        paginated_notifications = self.get_paginated_queryset(combined_notifications)

        context = {"request": request, "unread_count": unread_count}

        serializer = NotificationSerializer(
            paginated_notifications, context=context, many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def mark_as_read(
        self, request: Request, profile_uuid: uuid.UUID, notification_id: int
    ) -> Response:
        """
        Marks a specific notification as read.

        This method marks a notification, identified by its ID, as read. It ensures that the notification
        exists and belongs to the user making the request. If the notification is found and the user has
        the necessary permissions, the notification's 'is_read' status is updated.
        """
        try:
            profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist()
        try:
            notification = Notification.objects.get(pk=notification_id)
        except Notification.DoesNotExist:
            raise NotFound(detail="Notification not found")

        if notification.user != request.user:
            raise PermissionDenied(
                detail="You do not have permission to modify this notification"
            )

        serializer = NotificationSerializer(notification, context={"request": request})
        serializer.mark_read()
        return Response(serializer.data, status=status.HTTP_200_OK)
