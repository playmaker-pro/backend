from django.db import migrations


def add_notification_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")

    templates = [
        {
            "event_type": "query_pool_exhausted",
            "notification_type": "BI",
            "content_template": "Pula zapytań wyczerpana. Zwiększ limit.",
        },
        {
            "event_type": "inquiry_request_restored",
            "notification_type": "BI",
            "content_template": "Twoja pula zapytań została zwiększona.",
        },
        {
            "event_type": "pending_inquiry_decision",
            "notification_type": "BI",
            "content_template": "Zapytania oczekują na twoją decyzję.",
        },
        {
            "event_type": "reward_sender",
            "notification_type": "BI",
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
