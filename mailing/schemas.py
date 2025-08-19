from typing import List, Optional

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from pydantic import BaseModel

from backend.settings import cfg
from mailing.tasks import notify_admins, send

MAIL_TEMPLATES_DIR = cfg.smtp.templates_dir


class MailContent(BaseModel):
    subject: str = ""

    html_content: Optional[str] = None
    text_content: Optional[str] = None

    subject_format: str
    template_path: str

    class Config:
        use_enum_values = True

    def __call__(self, context: dict = dict()) -> "MailContent":
        self.render_content(context)
        return self

    def render_content(self, context: dict) -> None:
        """
        Renders the HTML body using the given context.
        """
        try:
            self.subject = self.subject_format.format(**context)
        except KeyError as e:
            raise ValueError(f"Some context keys are missing: {e}")

        self.html_content = render_to_string(self.template_path, context)
        self.text_content = strip_tags(self.html_content)

    @property
    def ready(self) -> bool:
        """
        Checks if the content is ready to be sent.
        """
        return self.html_content and self.text_content and self.subject

    @property
    def data(self) -> dict:
        """
        Gets the email data ready for sending.
        """
        if not self.ready:
            raise ValueError("Content is not ready.")

        return {
            "html_message": self.html_content,
            "message": self.text_content,
            "subject": self.subject,
        }


class Envelope(BaseModel):
    """
    Represents an email envelope with a subject and a list of recipients.
    """

    mail: MailContent
    recipients: List[str] = []

    def send(self, separate: bool = False) -> None:
        """
        Sends the email using the provided mail content and recipients.
        """
        if not self.recipients:
            raise ValueError("Recipients list cannot be empty.")

        send.delay(
            **self.mail.data,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(self.recipients),
            separate=separate,
        )

    def send_to_admins(self) -> None:
        """
        Sends the email to admins using the provided mail content.
        """
        notify_admins.delay(**self.mail.data)


class EmailTemplateRegistry:
    INQUIRY_LIMIT = MailContent(
        subject_format="Rozbuduj swoje transferowe możliwości – Rozszerz limit zapytań!",
        template_path=MAIL_TEMPLATES_DIR + "/inquiry_limit.html",
    )
    NEW_USER = MailContent(
        subject_format="Witaj na PlayMaker.pro. Potwierdź rejestrację konta.",
        template_path=MAIL_TEMPLATES_DIR + "/new_user.html",
    )
    PASSWORD_CHANGE = MailContent(
        subject_format="Zmiana hasła do Twojego konta.",
        template_path=MAIL_TEMPLATES_DIR + "/password_change.html",
    )
    PREMIUM_EXPIRED = MailContent(
        subject_format="⚠️ Twoje Premium wygasło – odnów je teraz!",
        template_path=MAIL_TEMPLATES_DIR + "/premium_expired.html",
    )
    REFERRAL_REWARD_REFERRED = MailContent(
        subject_format="Witaj w PlayMaker.pro! Odbierz swój prezent powitalny",
        template_path=MAIL_TEMPLATES_DIR + "/referral_reward_referred.html",
    )
    REFERRAL_REWARD_REFERRER_1 = MailContent(
        subject_format="Gratulacje! Otrzymujesz nagrodę za polecenie nowego użytkownika",
        template_path=MAIL_TEMPLATES_DIR + "/1_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_3 = MailContent(
        subject_format="Gratulacje! Nagroda za 3 skuteczne polecenia PlayMaker.pro",
        template_path=MAIL_TEMPLATES_DIR + "/3_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_5 = MailContent(
        subject_format="Gratulacje! Otrzymujesz miesiąc Premium i treningi za 5 poleceń PlayMaker.pro",
        template_path=MAIL_TEMPLATES_DIR + "/5_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_15 = MailContent(
        subject_format="Gratulacje! 6 miesięcy Premium za 15 poleceń PlayMaker.pro",
        template_path=MAIL_TEMPLATES_DIR + "/15_referral_reward_referrer.html",
    )
    ACCEPTED_INQUIRY = MailContent(
        subject_format="{related_role} {related_full_name} {verb} Twoje zapytanie o piłkarski kontakt!",
        template_path=MAIL_TEMPLATES_DIR + "/inquiries/accepted_inquiry.html",
    )
    REJECTED_INQUIRY = MailContent(
        subject_format="{related_role} {related_full_name} {verb} Twoje zapytanie o piłkarski kontakt!",
        template_path=MAIL_TEMPLATES_DIR + "/inquiries/rejected_inquiry.html",
    )
    NEW_INQUIRY = MailContent(
        subject_format="Masz nowe zapytanie o piłkarski kontakt!",
        template_path=MAIL_TEMPLATES_DIR + "/inquiries/new_inquiry.html",
    )
    OUTDATED_INQUIRY = MailContent(
        subject_format="Zwiększamy Twoją pulę zapytań o piłkarski kontakt!",
        template_path=MAIL_TEMPLATES_DIR + "/inquiries/outdated_inquiry.html",
    )
    OUTDATED_REMINDER = MailContent(
        subject_format="Masz zapytanie o piłkarski kontakt czekające na decyzję.",
        template_path=MAIL_TEMPLATES_DIR + "/inquiries/outdated_reminder.html",
    )
    SYSTEM_ERROR = MailContent(
        subject_format="{subject}",
        template_path=MAIL_TEMPLATES_DIR + "/system_error.html",
    )
    TEST = MailContent(
        subject_format="Testowy email",
        template_path=MAIL_TEMPLATES_DIR + "/test.html",
    )
