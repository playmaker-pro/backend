from django.test import TestCase
from notifications.models import NotificationTemplate
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationTemplateModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.get_or_create()

    def test_render_content(self) -> None:
        """
        Test the 'render_content' method of the NotificationTemplate model.
        This test checks if the method correctly replaces placeholders in the
        content template with values from the provided context.
        """
        # Create a notification template with placeholders
        template = NotificationTemplate.objects.create(
            event_type="test_event",
            notification_type="BI",
            content_template="Hello, {name}! You have new {event_type}.",
        )

        # Test with all required context data
        rendered_content = template.render_content(
            self.user, {"name": "XYZ", "event_type": "notification"}
        )
        assert rendered_content == "Hello, XYZ! You have new notification."
