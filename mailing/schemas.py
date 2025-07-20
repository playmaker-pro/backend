from typing import Optional

from django.template import engines
from django.utils.safestring import SafeText
from pydantic import BaseModel, root_validator


class MailContent(BaseModel):
    subject: Optional[str] = None
    subject_template_path: Optional[str] = None
    template_path: str

    @root_validator
    def check_subject_or_template(cls, values):
        """
        Validates that either 'subject' or 'subject_template_path' is provided, but not both.
        """
        subject = values.get("subject")
        subject_template_path = values.get("subject_template_path")

        if subject and subject_template_path:
            raise ValueError(
                "Only one of 'subject' or 'subject_template_path' can be provided."
            )
        if not subject and not subject_template_path:
            raise ValueError(
                "Either 'subject' or 'subject_template_path' must be provided."
            )
        return values

    def parse_template(self, context: dict) -> SafeText:
        """
        Renders the HTML body using the given context.
        """
        template_engine = engines["django"]
        return template_engine.get_template(self.template_path).render(context)

    def parse_subject(self, context: dict) -> str:
        """
        Renders the subject line using the given context, if a template path is provided,
        otherwise returns the static subject.
        """
        template_engine = engines["django"]

        if self.subject_template_path:
            return (
                template_engine.get_template(self.subject_template_path)
                .render(context)
                .strip()
            )
        return self.subject


class EmailTemplateRegistry:
    INQUIRY_LIMIT = MailContent(
        subject="Rozbuduj swoje transferowe możliwości – Rozszerz limit zapytań!",
        template_path="mailing/mails/inquiry_limit.html",
    )
    NEW_USER = MailContent(
        subject="Witaj na PlayMaker.pro. Potwierdź rejestrację konta.",
        template_path="mailing/mails/new_user.html",
    )
    PASSWORD_CHANGE = MailContent(
        subject="Zmiana hasła do Twojego konta.",
        template_path="mailing/mails/password_change.html",
    )
    PREMIUM_EXPIRED = MailContent(
        subject="⚠️ Twoje Premium wygasło – odnów je teraz!",
        template_path="mailing/mails/premium_expired.html",
    )
    REFERRAL_REWARD_REFERRED = MailContent(
        subject="Witaj w PlayMaker.pro! Odbierz swój prezent powitalny",
        template_path="mailing/mails/referral_reward_referred.html",
    )
    REFERRAL_REWARD_REFERRER_1 = MailContent(
        subject="Gratulacje! Otrzymujesz nagrodę za polecenie nowego użytkownika",
        template_path="mailing/mails/1_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_3 = MailContent(
        subject="Gratulacje! Nagroda za 3 skuteczne polecenia PlayMaker.pro",
        template_path="mailing/mails/3_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_5 = MailContent(
        subject="Gratulacje! Otrzymujesz miesiąc Premium i treningi za 5 poleceń PlayMaker.pro",
        template_path="mailing/mails/5_referral_reward_referrer.html",
    )
    REFERRAL_REWARD_REFERRER_15 = MailContent(
        subject="Gratulacje! 6 miesięcy Premium za 15 poleceń PlayMaker.pro",
        template_path="mailing/mails/15_referral_reward_referrer.html",
    )
    ACCEPTED_INQUIRY = MailContent(
        subject_template_path="mailing/mails/inquiries/accepted_inquiry_subject.txt",
        template_path="mailing/mails/inquiries/accepted_inquiry.html",
    )
    REJECTED_INQUIRY = MailContent(
        subject_template_path="mailing/mails/inquiries/rejected_inquiry_subject.txt",
        template_path="mailing/mails/inquiries/rejected_inquiry.html",
    )
    NEW_INQUIRY = MailContent(
        subject="Masz nowe zapytanie o piłkarski kontakt!",
        template_path="mailing/mails/inquiries/new_inquiry.html",
    )
    OUTDATED_INQUIRY = MailContent(
        subject="Zwiększamy Twoją pulę zapytań o piłkarski kontakt!",
        template_path="mailing/mails/inquiries/outdated_inquiry.html",
    )
    OUTDATED_REMINDER = MailContent(
        subject="Masz zapytanie o piłkarski kontakt czekające na decyzję.",
        template_path="mailing/mails/inquiries/outdated_reminder.html",
    )

    @classmethod
    def get(cls, name: str) -> MailContent:
        try:
            return getattr(cls, name)
        except AttributeError:
            raise ValueError(f"Unknown template config key: {name}")
