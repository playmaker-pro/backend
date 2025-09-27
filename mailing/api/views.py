from uuid import UUID

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.views import EndpointView
from mailing.api.serializers import MailingPreferencesSerializer
from mailing.models import MailingPreferences


class MailingAPIEndpoint(EndpointView):
    authentication_classes = [IsAuthenticated]

    def get_my_preferences(self, request: Request) -> Response:
        preferences = request.user.mailing.preferences
        serializer = MailingPreferencesSerializer(preferences)
        return Response(serializer.data)

    def update_my_preferences(self, request: Request) -> Response:
        preferences = request.user.mailing.preferences
        serializer = MailingPreferencesSerializer(
            preferences, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["GET"])
def update_preferences_directly(
    request: Request, preferences_uuid: UUID, mailing_type: str
) -> HttpResponse:
    if not preferences_uuid or not mailing_type:
        return Response(
            {"detail": "Missing uuid or mailing parameter."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        mailing_preferences = MailingPreferences.objects.get(uuid=preferences_uuid)
    except MailingPreferences.DoesNotExist:
        return Response(
            {"detail": "Mailing preferences not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    update_data = {mailing_type: False}
    serializer = MailingPreferencesSerializer(
        mailing_preferences, data=update_data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return HttpResponse(
        "<h1><center>Preferencje zostały zaktualizowane</center></h1>", status=200
    )
