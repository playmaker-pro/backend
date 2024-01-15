from typing import Tuple, cast
import re


def extract_uidb64_and_token_from_email(email_content: str) -> Tuple[str, str]:
    """Extract uidb64 and token values from the email content."""
    pattern = r"/password/reset/new-password/(\w+)/([\w-]+)/"
    match = re.search(pattern, email_content)
    if match:
        return cast(Tuple[str, str], match.groups())
    raise ValueError("Failed to extract uidb64 and token from email content.")
