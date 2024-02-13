import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

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

    def create_basic_inquiry_plan(self, user) -> None:
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
