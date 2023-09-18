from rest_framework import status
from rest_framework.response import Response

from api.custom_throttling import LimitFeatureNotificationEndpoint
from api.views import EndpointView
from features.serializers import FutureFeatureSerializer


class FeatureElementAPI(EndpointView):
    throttle_classes = [LimitFeatureNotificationEndpoint]

    def create_feature_subscription_entity(self, request):
        """
        Create feature subscription entity.
        """
        data: dict = request.data
        data["user"] = request.user.id
        serializer = FutureFeatureSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
