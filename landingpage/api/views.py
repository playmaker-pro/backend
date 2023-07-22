import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics  # noqa
from rest_framework import permissions, status  # noqa
from rest_framework.response import Response  # noqa

from products.models import Product, Request  # noqa
from users.models import User  # noqa

from .decorators import is_owner
from .serializers import TestFormSerializer

logger = logging.getLogger(__name__)


class TestFormAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    serializer_class = TestFormSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ["post", "patch"]
    model = Request
    queryset = Request.objects.all()

    def perform_create(self, serializer):
        return serializer.save()

    def post(self, request, *args, **kwargs):
        data = request.data

        name = "Wsparcie transferowe dla piłkarza"

        product = Product.objects.filter(title=name)
        user = User.objects.filter(pk=data["user"])

        if not user or not product.exists() or (len(user) >= 2 or len(product) >= 2):
            logger.error("User or product couldn't be found")
            return Response(
                {"error": "User or product couldn't be found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        date_now = timezone.now().strftime("%Y-%m-%d")
        user = user.first()
        product_id = product.first().id
        user_team = user.profile.get_team()
        try:
            data = {
                "product": product_id,
                "user": user.id,
                "raw_body": {
                    "nr": f"{user.id}{product_id}{date_now}".replace("-", ""),
                    "name": user.display_full_name,
                    "team": user_team.name if user_team else "",
                    "parent_league": user_team.display_league_top_parent
                    if user_team
                    else "",
                    "user voivodeship": user.profile.voivodeship_obj.name
                    if user.profile.voivodeship_obj
                    else "",
                    "city": data.get("city"),
                    "leagues": data.get("leagues"),
                    "distance": data.get("distance"),
                    "email": user.email,
                    "profile": f"{request.META['HTTP_HOST']}/users/{user.profile.slug}",
                    "phone": user.profile.phone,
                    "date": date_now,
                },
            }
        except Exception as e:
            logger.error(e)
            return Response({"error": "Ups, coś poszło nie tak"})

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        new_data = self.perform_create(serializer)

        try:
            new_data.send_notification_to_admin()
            logger.info(f"Mail sent: {serializer.data}")

        except Exception as e:
            logger.error(f"Mail could not be sent {e}")

        return Response({"success": new_data.id}, status=status.HTTP_201_CREATED)

    @is_owner(query=queryset)
    def patch(self, request, *args, **kwargs):
        request_help = get_object_or_404(self.queryset, id=kwargs.get("pk"))
        data = request_help.raw_body

        request.data.pop("user")

        data["videos"] = request.data.get("videos")
        data["comment"] = request.data.get("comment")

        request.data["raw_body"] = data
        self.partial_update(request, *args, **kwargs)

        try:
            request_help.send_notification_to_admin()
            logger.info(f"Mail sent: {data}")

        except Exception as e:
            logger.error(f"Mail could not be sent {e}")

        return Response(
            {"success": "Successfully updated"}, status=status.HTTP_201_CREATED
        )
