import re


def get_notification_redirect_url(event_type: str, details: dict, base_url: str) -> str:
    """
    Generates a redirect URL based on the event type and details of the notification.
    """
    # Define URL mapping for different event types and roles
    URL_MAPPING = {
        "accept_inquiry": "inquiries/my/contacts",  # URL for sender when inquiry is accepted
        "reject_inquiry": "inquiries/my/sent",  # URL for sender when inquiry is rejected
        "receive_inquiry": "inquiries/my/received",  # URL for recipient when they receive an inquiry
    }

    # Use the event type to determine the redirect URL
    if event_type in URL_MAPPING:
        return f"{base_url}{URL_MAPPING[event_type]}"

    # Fallback to a default URL if specific mapping isn't found
    return base_url


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
