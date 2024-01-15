import logging as _logging
import re as _re
import traceback as _traceback
from typing import List as _List

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

from mailing.schemas import EmailSchema as _EmailSchema

logger: _logging.Logger = _logging.getLogger("mailing")


class MailingService:
    def __init__(self, schema: _EmailSchema) -> None:
        self._schema: _EmailSchema = schema

    @property
    def _subject(self) -> str:
        """Return email subject."""
        return self._schema.subject

    @property
    def _body(self) -> str:
        """Return email body."""
        return self._schema.body

    @property
    def _recipients(self) -> _List:
        """Return email recipients."""
        return self._schema.recipients

    @property
    def _sender(self) -> str:
        """Return email sender."""
        return self._schema.sender

    def send_mail(self) -> None:
        """Send email based on schema. Log error if sending failed."""
        try:
            send_mail(
                subject=self._subject,
                message=self._body,
                from_email=self._sender,
                recipient_list=self._recipients,
            )
        except Exception as e:
            logger.error(f"[ERROR]\n{self._schema.log}\n{e}\n{_traceback.format_exc()}")
        else:
            logger.info(f"[SUCCESS]\n{self._schema.log}")


class MessageContentParser:
    def __init__(self, recipient: settings.AUTH_USER_MODEL, **extra_kwargs) -> None:
        self._recipient: settings.AUTH_USER_MODEL = recipient
        self._text: str = ""
        self._extra_kwargs = extra_kwargs

    @property
    def text(self) -> str:
        return str(self._text)

    @text.setter
    def text(self, value: str) -> None:
        self._text = _(value)

    @property
    def _recipient_user_gender_index(self) -> int:
        """Return 1 if related user is female, 0 otherwise"""
        return int(self._recipient.userpreferences.gender == "K")

    def _put_correct_form(self) -> None:
        """Replace '#male_form|female_form#' with correct form of word based on recipient gender."""
        pattern = r"#(\w+)\|(\w+)#"

        matches = _re.findall(pattern, self.text)
        _id = self._recipient_user_gender_index

        for match in matches:
            self._text = self._text.replace(
                f"#{match[0]}|{match[1]}#", str(_(match[_id]))
            )

    def _put_url(self) -> None:
        """Replace '#url#' with url."""
        url = self._extra_kwargs.get("url", "")
        self._text = self._text.replace("#url#", url)

    def parse_email_title(self, content: str) -> str:
        """Transform text and return correct form of email_title."""
        self.text = content

        return self.text

    def parse_email_body(self, content: str) -> str:
        """Transform text and return correct form of email_body."""
        self.text = content
        self._put_url()
        self._put_correct_form()

        return self.text
