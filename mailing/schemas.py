from enum import Enum
from typing import List, Optional

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from pydantic import BaseModel, ConfigDict


class EmailType(str, Enum):
    INQUIRY_LIMIT = "inquiry_limit"
    NEW_USER = "new_user"
    PASSWORD_CHANGE = "password_change"
    PREMIUM_EXPIRED = "premium_expired"
    REFERRAL_REWARD = "referral_reward"
    SYSTEM = "system"
    INQUIRY_ACTION = "inquiry_action"


class MailContent(BaseModel):
    subject: str
    template_path: str
    email_type: EmailType = EmailType.SYSTEM

    _html_content: str = ""
    _text_content: str = ""
    model_config = ConfigDict(use_enum_values=True)

    def __call__(self, context: Optional[dict] = dict()) -> None:
        self.render_content(context)

    def render_content(self, context: dict) -> dict:
        """
        Renders the HTML body using the given context.
        """
        try:
            self.subject = self.subject.format(**context)
        except KeyError as e:
            raise ValueError(f"Some context keys are missing: {e}")

        self._html_content = render_to_string(self.template_path, context)
        self._text_content = strip_tags(self._html_content)
        return self.data

    @property
    def data(self) -> dict:
        """
        Example property to demonstrate usage.
        """
        if not self.ready:
            raise ValueError("Content is not ready.")

        return {
            "html_message": self._html_content,
            "message": self._text_content,
            "subject": self.subject,
        }

    @property
    def ready(self) -> bool:
        """
        Check if the content is ready to be sent.
        """
        return self._html_content and self._text_content


class Envelope(BaseModel):
    """
    Represents an email envelope with a subject and a list of recipients.
    """

    mail: MailContent
    recipients: List[str]


class EmailTemplateRegistry:
    INQUIRY_LIMIT = MailContent(
        subject="Rozbuduj swoje transferowe możliwości – Rozszerz limit zapytań!",
        template_path="inquiry_limit.html",
        email_type=EmailType.INQUIRY_LIMIT,
    )
    NEW_USER = MailContent(
        subject="Witaj na PlayMaker.pro. Potwierdź rejestrację konta.",
        template_path="new_user.html",
        email_type=EmailType.NEW_USER,
    )
    PASSWORD_CHANGE = MailContent(
        subject="Zmiana hasła do Twojego konta.",
        template_path="password_change.html",
        email_type=EmailType.PASSWORD_CHANGE,
    )
    PREMIUM_EXPIRED = MailContent(
        subject="⚠️ Twoje Premium wygasło – odnów je teraz!",
        template_path="premium_expired.html",
        email_type=EmailType.PREMIUM_EXPIRED,
    )
    REFERRAL_REWARD_REFERRED = MailContent(
        subject="Witaj w PlayMaker.pro! Odbierz swój prezent powitalny",
        template_path="referral_reward_referred.html",
        email_type=EmailType.REFERRAL_REWARD,
    )
    REFERRAL_REWARD_REFERRER_1 = MailContent(
        subject="Gratulacje! Otrzymujesz nagrodę za polecenie nowego użytkownika",
        template_path="1_referral_reward_referrer.html",
        email_type=EmailType.REFERRAL_REWARD,
    )
    REFERRAL_REWARD_REFERRER_3 = MailContent(
        subject="Gratulacje! Nagroda za 3 skuteczne polecenia PlayMaker.pro",
        template_path="3_referral_reward_referrer.html",
        email_type=EmailType.REFERRAL_REWARD,
    )
    REFERRAL_REWARD_REFERRER_5 = MailContent(
        subject="Gratulacje! Otrzymujesz miesiąc Premium i treningi za 5 poleceń PlayMaker.pro",
        template_path="5_referral_reward_referrer.html",
        email_type=EmailType.REFERRAL_REWARD,
    )
    REFERRAL_REWARD_REFERRER_15 = MailContent(
        subject="Gratulacje! 6 miesięcy Premium za 15 poleceń PlayMaker.pro",
        template_path="15_referral_reward_referrer.html",
        email_type=EmailType.REFERRAL_REWARD,
    )
    ACCEPTED_INQUIRY = MailContent(
        subject="{who} {verb} Twoje zapytanie o piłkarski kontakt!",
        template_path="inquiries/accepted_inquiry.html",
        email_type=EmailType.INQUIRY_ACTION,
    )
    REJECTED_INQUIRY = MailContent(
        subject="{who} {verb} Twoje zapytanie o piłkarski kontakt!",
        template_path="inquiries/rejected_inquiry.html",
        email_type=EmailType.INQUIRY_ACTION,
    )
    NEW_INQUIRY = MailContent(
        subject="Masz nowe zapytanie o piłkarski kontakt!",
        template_path="inquiries/new_inquiry.html",
        email_type=EmailType.INQUIRY_ACTION,
    )
    OUTDATED_INQUIRY = MailContent(
        subject="Zwiększamy Twoją pulę zapytań o piłkarski kontakt!",
        template_path="inquiries/outdated_inquiry.html",
        email_type=EmailType.INQUIRY_ACTION,
    )
    OUTDATED_REMINDER = MailContent(
        subject="Masz zapytanie o piłkarski kontakt czekające na decyzję.",
        template_path="inquiries/outdated_reminder.html",
        email_type=EmailType.INQUIRY_ACTION,
    )
