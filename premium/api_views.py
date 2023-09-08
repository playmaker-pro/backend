from rest_framework.views import APIView
from . import serializers
from rest_framework import status
from rest_framework.response import Response


class PremiumRequestAPIView(APIView):
    serializer_class = serializers.PremiumRequestSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
