from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from api.base_view import EndpointView
from labels.api.serializers import LabelDefinitionSerializer
from labels.models import LabelDefinition


class LabelsAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_labels_definition(self, request: Request) -> Response:
        """
        Retrieves all label definitions and returns them in a serialized format.
        """
        available_labels = LabelDefinition.objects.all()
        serializer = LabelDefinitionSerializer(available_labels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
