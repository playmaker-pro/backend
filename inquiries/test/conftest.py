from unittest.mock import patch

import pytest

from inquiries.models import UserInquiry as _UserInquiry
from utils.factories.inquiry_factories import UserInquiryFactory as _UserInquiryFactory


@pytest.fixture
def silence_mails():
    """Silence all mails"""
    with patch("mailing.services.MailingService.send_mail") as mck:
        yield mck


@pytest.fixture
def user_inquiry_on_limit() -> _UserInquiry:
    """Return UserInquiry with 5/5 inquiries"""
    yield _UserInquiryFactory.create(counter=5)
