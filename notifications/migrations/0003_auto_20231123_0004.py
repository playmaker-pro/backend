from django.db import migrations

from notifications.models import Notification as _Notification


def add_notification_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")

    templates = [
        {
            "event_type": _Notification.EventType.QUERY_POOL_EXHAUSTED,
            "notification_type": _Notification.NotificationType.BUILT_IN,
            "content_template": "Pula zapytań wyczerpana. Zwiększ limit.",
        },
        {
            "event_type": _Notification.EventType.INQUIRY_REQUEST_RESTORED,
            "notification_type": _Notification.NotificationType.BUILT_IN,
            "content_template": "Twoja pula zapytań została zwiększona.",
        },
        {
            "event_type": _Notification.EventType.PENDING_INQUIRY_DECISION,
            "notification_type": _Notification.NotificationType.BUILT_IN,
            "content_template": "Zapytania oczekują na twoją decyzję.",
        },
        {
            "event_type": _Notification.EventType.REWARD_SENDER,
            "notification_type": _Notification.NotificationType.BUILT_IN,
            "content_template": "Twoja pula zapytań została zwiększona",
        },
    ]

    for template_data in templates:
        NotificationTemplate.objects.create(**template_data)


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_notification_notificationtemplate"),
    ]

    operations = [migrations.RunPython(add_notification_templates)]
