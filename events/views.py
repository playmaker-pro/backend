from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from api import errors as base_errors
from api.views import EndpointView

from events import services, serializers, errors


User = get_user_model()


class EventsAPI(EndpointView):
    service = services.NotificationServices()

    def read_event(self, request: Request, event_id: int) -> Response:
        """Mark event as seen by user."""
        try:
            self.service.read_event(event_id, request.user.id)
        except errors.EventAlreadySeen:
            return Response(status=status.HTTP_409_CONFLICT)
        except errors.OperationOnEventNotAllowed:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            raise base_errors.HTTPObjectDoesNotExists(f"Failed due: {e}")

        return Response(status=status.HTTP_200_OK)

    def get_user_events(self, request: Request, user_id: int) -> Response:
        """Returns list of events belong to a user."""
        # TODO(rkesik): since there is no other cases this enpoints returns only UNSEEN events
        # later if there will be need we can add query params to make it more generic.
        # see: get_user_unseen_events
        try:
            events: QuerySet = self.service.get_user_unseen_events(
                user_id, request.user.id
            )
        except errors.OperationOnEventNotAllowed:
            return Response(status=status.HTTP_403_FORBIDDEN)
        paginated = self.paginate_queryset(events)

        serializer = serializers.EventMessageSerializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)
