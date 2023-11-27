from django.conf import settings
from django.utils.translation import gettext_lazy as _

from mailing.services import MessageContentParser as _MessageContentParser

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


class InquiryMessageContentParser(_MessageContentParser):
    """Parse text into a list of words."""

    def __init__(
        self, log_instance: "inquiries.models.UserInquiryLog", **extra_kwargs
    ) -> None:
        self._log: "inquiries.models.UserInquiryLog" = log_instance
        super().__init__(recipient=self._recipient_user, **extra_kwargs)

    @property
    def parse_log_body(self) -> str:
        """
        Set text as log body.
        Transform text and return correct form of log_body.
        """
        self.text = self._log.message.log_body
        self._put_recipient_full_name()

        return self.text

    @property
    def parse_email_body(self) -> str:
        """
        Set text as email body.
        Transform text and return correct form of email_body.
        """
        self.text = self._log.message.email_body
        self._put_correct_form()
        self._put_recipient_full_name()
        self._put_related_user_with_role()
        self._put_related_user_with_role_in_objective_case()
        self._put_url()

        return self.text

    @property
    def parse_email_title(self) -> str:
        """
        Set text as email title.
        Transform text and return correct form of email_title.
        """
        self.text = self._log.message.email_title
        self._put_correct_form()
        self._put_recipient_full_name()
        self._put_related_user_with_role()
        self._put_related_user_with_role_in_objective_case()

        return self.text

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

    def _put_recipient_full_name(self) -> None:
        """Replace '<>' with recipient full name."""
        self._text = self._text.replace(
            "<>", f"{self._recipient_user.display_full_name}"
        )

    def _put_related_user_with_role(self) -> None:
        """Replace '#r#' with related user full name and role."""
        role = _(
            GENDER_BASED_ROLES[self._related_user.declared_role][
                self._related_user_gender_index
            ]
        )
        self._text = self._text.replace(
            "#r#", f"{role} {self._related_user.display_full_name}"
        )

    def _put_related_user_with_role_in_objective_case(self) -> None:
        """Replace '#rb#' with related user full name and role in objective case (biernik)."""
        role = _(
            OBJECTIVE_GENDER_BASED_ROLES[self._related_user.declared_role][
                self._related_user_gender_index
            ]
        )
        self._text = self._text.replace(
            "#rb#", f"{role} {self._related_user.display_full_name}"
        )
