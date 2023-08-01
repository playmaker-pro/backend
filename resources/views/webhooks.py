from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated  # <-- Here
from rest_framework.response import Response
from rest_framework.views import APIView


class WebhookPlayer(
    APIView
):  # TODO(bartnyk): prolly whole app can be removed, unused resource
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        player_id = request.data.get("user_id")

        if player_id:
            player_id = int(player_id)
            from profiles.models import PlayerProfile

            try:
                player = PlayerProfile.objects.get(
                    mapper__mapperentity__related_type="player",
                    mapper__mapperentity__database_source="s38",
                    mapper__mapperentity__mapper_id=player_id,
                )
                player.refresh_metrics(event_log_msg="Triggered by s38 as a webook.")
                content = {f"data refreshed. for player={player} player-id:{player_id}"}

            except PlayerProfile.DoesNotExist:
                content = {f"data do not exists for that ID {player_id}"}

            except PlayerProfile.MultipleObjectsReturned:
                player = PlayerProfile.objects.filter(
                    mapper__mapperentity__related_type="player",
                    mapper__mapperentity__database_source="s38",
                    mapper__mapperentity__mapper_id=player_id,
                ).first()
                player.refresh_metrics(event_log_msg="Triggered by s38 as a webook")
                content = {f"data refreshed. for player={player} player-id:{player_id}"}
        else:
            content = {"No user with given data"}
        return Response(content)
