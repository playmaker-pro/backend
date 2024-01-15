import re

from notifications.models import Notification


def get_notification_redirect_url(
    event_type: Notification.EventType, details: dict
) -> str:
    """
    Generates a namespaced URL path based on the event type of the notification.

    This function maps each event type to a specific URL name defined in the Django URL configuration.
    It is used to provide a relevant redirect path for each type of notification.
    """
    URL_MAPPING = {
        Notification.EventType.ACCEPT_INQUIRY: "api:inquiries:my_inquiry_contacts",
        Notification.EventType.REJECT_INQUIRY: "api:inquiries:my_sent_inquiries",
        Notification.EventType.RECEIVE_INQUIRY: "api:inquiries:my_received_inquiries",
        Notification.EventType.QUERY_POOL_EXHAUSTED: "api:inquiries:my_sent_inquiries",
        Notification.EventType.PENDING_INQUIRY_DECISION: "api:inquiries:my_received_inquiries",
        Notification.EventType.REWARD_SENDER: "api:inquiries:my_sent_inquiries",
        Notification.EventType.INQUIRY_REQUEST_RESTORED: "api:inquiries:my_sent_inquiries",
    }

    return URL_MAPPING.get(event_type, "")


class NotificationContentParser:
    def __init__(self, user, **context):
        self.user = user
        self.context = context

    def parse(self, template_content: str) -> str:
        """
        Parses the notification template content and replaces placeholders with actual values.
        """
        # Replace placeholders for user attributes
        content = template_content.format(**self.context)

        # Handle gender-specific language
        content = self.handle_gender_specific_language(content)
        return content

    def handle_gender_specific_language(self, content: str) -> str:
        """
        Handles gender-specific language in the content based on the user's gender.
        """
        gender = self.context.get(
            "sender_gender", "M"
        )  # Default to "M" if gender is not provided
        gender_index = 1 if gender == "K" else 0
        pattern = r"#(\w+)\|(\w+)#"
        matches = re.findall(pattern, content)
        for male_form, female_form in matches:
            replacement = female_form if gender_index == 1 else male_form
            content = content.replace(f"#{male_form}|{female_form}#", replacement)
        return content
