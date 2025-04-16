from rest_framework import routers

router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    # path(
    #     r"<uuid:profile_uuid>",
    #     view.UserNotificationView.as_view({"get": "get_notifications"}),
    #     name="get_user_notifications",
    # ),
    # path(
    #     "<uuid:profile_uuid>/<int:notification_id>/",
    #     view.UserNotificationView.as_view({"patch": "mark_as_read"}),
    #     name="mark_notification_read",
    # ),
]
