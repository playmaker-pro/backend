from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # <-- Here


class WebhookPlayer(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        player_id = request.POST.get("user_id")
        if player_id:
            from profiles.models import PlayerProfile
            try:
                player = PlayerProfile.objects.get(data_mapper_id=player_id)
                player.refresh_metrics(event_log_msg="Triggered by s38 as a webook")
            except PlayerProfile.DoesNotExist:
                content = {"data do not exists for that ID"}
            
        return Response(content)
