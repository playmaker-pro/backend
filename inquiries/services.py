import datetime
import logging
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from mailing.services import TransactionalEmailService
from mailing.models import UserEmailOutbox
from mailing.constants import EmailTypes, EmailTemplates
from inquiries.models import INQUIRY_LIMIT_INCREASE_URL

from .models import InquiryPlan, InquiryRequest, UserInquiry

logger: logging.Logger = logging.getLogger(__name__)
User = get_user_model()


class InquireService:
    def create_default_basic_plan_for_coach_if_not_present(self):
        args = settings.INQUIRIES_INITAL_PLAN_COACH
        try:
            plan = InquiryPlan.objects.get(name=args["name"])

        except InquiryPlan.DoesNotExist:
            logger.info(
                "Initial InquiryPlan for coaches does not exists. Creating new one."
            )
            plan = InquiryPlan.objects.create(**args)
        return plan

    @staticmethod
    def create_basic_inquiry_plan(user) -> None:
        """Create basic inquiry plan and contact instance for user"""
        plan = InquiryPlan.basic()
        UserInquiry.objects.get_or_create(user=user, plan=plan)
        logger.info(f"Created {plan.description} plan for {user}")

    def create_default_basic_plan_if_not_present(self) -> InquiryPlan:
        """
        In case when there is no Default plan we would like to create it at first time
        """

        args = settings.INQUIRIES_INITAL_PLAN
        try:
            default = InquiryPlan.objects.get(default=True)
        except InquiryPlan.DoesNotExist:
            default = InquiryPlan.objects.create(**args)
        return default

    @staticmethod
    def unseen_requests(queryset, user: User) -> QuerySet:
        return queryset.filter(recipient=user, status__in=InquiryRequest.UNSEEN_STATES)

    @staticmethod
    def unseen_user_requests(user: User) -> QuerySet:
        return InquiryRequest.objects.filter(
            recipient=user, status=InquiryRequest.STATUS_SENT
        )

    @staticmethod
    def update_requests_with_read_status(queryset: QuerySet, user: User) -> None:
        for request in queryset.filter(status=InquiryRequest.STATUS_SENT):
            if request.recipient == user:
                request.read()
                request.save()

    @staticmethod
    def get_user_sent_inquiries(user: User) -> QuerySet:
        """Get all sent inquiries by user"""
        return user.sender_request_recipient.all().order_by("-created_at")

    @staticmethod
    def get_user_contacts(user: User) -> QuerySet:
        """Get all inquiries contacts by user"""
        return user.inquiries_contacts.order_by("-updated_at")

    @classmethod
    def get_user_received_inquiries(cls, user: User) -> QuerySet:
        """Get all received inquiries by user"""
        # queryset = user.inquiry_request_recipient.all().order_by("-created_at")

        # FIXME: Temporary we do not want to show old requests
        till_date = datetime.date(2024, 1, 21)
        queryset = user.inquiry_request_recipient.filter(
            created_at__gte=till_date
        ).order_by("-created_at")
        cls.update_requests_with_read_status(queryset, user)
        return queryset

    @staticmethod
    def get_user_inquiry_metadata(user: User) -> UserInquiry:
        """Get all received inquiries by user"""

        return user.userinquiry

    @staticmethod
    def update_inquiry_read_status_based_on_role(user: User) -> None:
        """
        Updates the read status of inquiries based on the role of the user.

        This method checks both sent and received inquiries for a given user.
        For received inquiries. it marks them as read by the recipient if they haven't
        been marked as such already. Similarly, for sent inquiries, it marks them as
        read by the sender, indicating that the sender has acknowledged any responses
        or actions taken by the recipient on those inquiries.
        """
        # Update received inquiries as read by the recipient
        InquiryRequest.objects.filter(
            recipient=user, is_read_by_recipient=False
        ).update(is_read_by_recipient=True)

        # Update received inquiries as read by the sender
        InquiryRequest.objects.filter(sender=user, is_read_by_sender=False).update(
            is_read_by_sender=True
        )

    def send_inquiry_limit_reached_email(self, user: settings.AUTH_USER_MODEL, force_send: bool = False) -> None:
        """Send email notification about reaching the limit"""
        if (
            self.can_sent_inquiry_limit_reached_email(user)
            or force_send
        ):
            parser = TransactionalEmailService(user=user, context={'url': INQUIRY_LIMIT_INCREASE_URL})
            parser.send(EmailTemplates.INQUIRY_LIMIT, EmailTypes.INQUIRY_LIMIT)

    def send_inquiry_log_email(self, log) -> None:
        """Send email to user with new inquiry request state"""
        url = log.ulr_to_profile
        sender = getattr(log.ref, "sender", None)
        TransactionalEmailService(log.log_owner.user, log=log, context={'url': url, 'sender': sender}).send(log.log_type, "inquiry_log")

    @staticmethod
    def can_sent_inquiry_limit_reached_email(
            user: settings.AUTH_USER_MODEL
    ) -> bool:
        """
        Return True if user can receive inquiry limit reached email.

        Send email once per round. So:
        - if last email was sent in april current year, we can sent next email after june current year.
        - if last email was sent in july current year, we can sent next email after december current year.
        - if last email was sent in december last year, we can sent next email after june current year.
        """
        curr_date = timezone.now()
        if not (
                last_sent_mail := (
                        UserEmailOutbox.objects.filter(
                            recipient=user.contact_email,
                            email_type=EmailTypes.INQUIRY_LIMIT,
                        ).last()
                )
        ):
            return True
        last_sent_mail = last_sent_mail.sent_date
        if last_sent_mail.month < 6:
            # last_sent | current_date | result
            # 2023-04-01 | 2023-06-01 | True
            # 2023-04-01 | 2023-05-01 | False
            # 2023-04-01 | 2025-04-01 | True
            return (
                True
                if (curr_date.month >= 6 and curr_date.year >= last_sent_mail.year)
                   or curr_date.year > last_sent_mail.year + 1
                else False
            )
        elif last_sent_mail.month == 12:
            # last_sent | current_date | result
            # 2022-12-03 | 2023-06-01 | True
            # 2022-12-03 | 2024-04-01 | True
            # 2022-12-03 | 2023-04-01 | False
            return (
                True
                if (curr_date.month >= 6 and curr_date.year > last_sent_mail.year)
                   or curr_date.year > last_sent_mail.year + 1
                else False
            )
        elif last_sent_mail.month >= 6:
            # last_sent | current_date | result
            # 2023-06-01 | 2023-12-01 | True
            # 2023-07-01 | 2023-11-01 | False
            # 2023-07-01 | 2025-11-01 | True
            return (
                True
                if curr_date.month == 12 or curr_date.year > last_sent_mail.year
                else False
            )