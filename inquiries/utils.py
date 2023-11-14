import re as _re

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

GENDER_BASED_ROLES = {
    "P": ("Piłkarz", "Piłkarka"),
    "T": ("Trener", "Trenerka"),
    "C": ("Działacz klubowy", "Działaczka klubowa"),
    "G": ("Kibic", "Kibic"),
    "M": ("Manager", "Manager"),
    "R": ("Sędzia", "Sędzia"),
    "S": ("Skaut", "Skaut"),
    None: ("", ""),
}
OBJECTIVE_GENDER_BASED_ROLES = {
    "P": ("piłkarza", "piłkarkę"),
    "T": ("trenera", "trenerkę"),
    "C": ("działacza klubowego", "działaczkę klubową"),
    "G": ("kibica", "kibica"),
    "M": ("managera", "managera"),
    "R": ("sędziego", "sędziego"),
    "S": ("skauta", "skauta"),
    None: ("", ""),
}


class TextParser:
    """Parse text into a list of words."""

    def __init__(self, log_instance: "inquiries.models.UserInquiryLog"):
        self._log: "inquiries.models.UserInquiryLog" = log_instance
        self._text: str = ""

    @property
    def log_body(self) -> str:
        """
        Set text as log body.
        Transform text and return correct form of log_body.
        """
        self._text = self._log.message.log_body
        self._text = _(self._text)
        self.put_recipient_full_name()
        return self._text

    @property
    def email_body(self) -> str:
        """
        Set text as email body.
        Transform text and return correct form of email_body.
        """
        self._text = self._log.message.email_body
        self.put_correct_form()
        self._text = _(self._text)
        self.put_recipient_full_name()
        self.put_related_user_with_role()
        self.put_related_user_with_role_in_objective_case()

        return self._text

    @property
    def email_title(self) -> str:
        """
        Set text as email title.
        Transform text and return correct form of email_title.
        """
        self._text = self._log.message.email_title
        self.put_correct_form()
        self._text = _(self._text)
        self.put_recipient_full_name()
        self.put_related_user_with_role()
        self.put_related_user_with_role_in_objective_case()

        return self._text

    @property
    def _recipient_user(self) -> settings.AUTH_USER_MODEL:
        """Return recipient user instance."""
        return self._log.log_owner.user

    @property
    def _related_user(self) -> settings.AUTH_USER_MODEL:
        """Return related user instance."""
        return self._log.related_with.user

    @property
    def _related_user_gender_index(self) -> int:
        """Return 1 if related user is female, 0 otherwise"""
        return int(self._related_user.userpreferences.gender == "K")

    @property
    def _recipient_user_gender_index(self) -> int:
        """Return 1 if related user is female, 0 otherwise"""
        return int(self._recipient_user.userpreferences.gender == "K")

    def put_recipient_full_name(self) -> None:
        """Replace '<>' with recipient full name."""
        self._text = self._text.replace(
            "<>", f"{self._recipient_user.display_full_name}"
        )

    def put_related_user_with_role(self) -> None:
        """Replace '#r#' with related user full name and role."""
        role = _(
            GENDER_BASED_ROLES[self._related_user.declared_role][
                self._related_user_gender_index
            ]
        )
        self._text = self._text.replace(
            "#r#", f"{role} {self._related_user.display_full_name}"
        )

    def put_related_user_with_role_in_objective_case(self) -> None:
        """Replace '#rb#' with related user full name and role in objective case (biernik)."""
        role = _(
            OBJECTIVE_GENDER_BASED_ROLES[self._related_user.declared_role][
                self._related_user_gender_index
            ]
        )
        self._text = self._text.replace(
            "#rb#", f"{role} {self._related_user.display_full_name}"
        )

    def put_correct_form(self) -> None:
        """Replace '#male_form|female_form#' with correct form of word based on recipient gender."""
        pattern = r"#(\w+)\|(\w+)#"
        matches = _re.findall(pattern, self._text)
        _id = self._recipient_user_gender_index

        for match in matches:
            self._text = self._text.replace(
                f"#{match[0]}|{match[1]}#", str(_(match[_id]))
            )


class InquiryMailManager:
    def __init__(self, log: "inquiries.models.UserInquiryLog") -> None:
        self._log = log

    @property
    def _recipient_email_address(self) -> str:
        """Return recipient email address."""
        return self._log.log_owner.user.inquiry_contact._email

    @property
    def _subject(self) -> str:
        """Return email subject."""
        return self._log.email_title

    @property
    def _body(self) -> str:
        """Return email body."""
        return self._log.email_body

    @classmethod
    def send_mail(cls, log: "inquiries.models.UserInquiryLog") -> None:
        """Send email based on log message."""
        instance = cls(log)
        send_mail(
            subject=instance._subject,
            message=instance._body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance._recipient_email_address],
        )
