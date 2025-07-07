import re
import html
from typing import Tuple, cast


def extract_uidb64_and_token_from_email(email_content: str) -> Tuple[str, str]:
    """Extract uidb64 and token values from the email content."""
    # Unescape HTML entities like &amp; -> &
    decoded_content = html.unescape(email_content)

    pattern = r"\buidb64=(\w+)&token=([\w-]+)"
    match = re.search(pattern, decoded_content)
    if match:
        return cast(Tuple[str, str], match.groups())
    raise ValueError("Failed to extract uidb64 and token from email content.")
