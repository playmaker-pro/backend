from unittest.mock import patch

import pytest


@pytest.fixture
def silence_mails():
    """Silence all mails"""
    with patch("inquiries.utils.InquiryMailManager.send_mail") as mck:
        yield mck
