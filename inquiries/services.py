import logging
from .models import InquiryRequest, InquiryPlan, UserInquiry
from django.conf import settings

logger: logging.Logger = logging.getLogger(__name__)


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

    def set_user_inquiry_plan(self, user):
        try:
            UserInquiry.objects.get(user=user)
        except UserInquiry.DoesNotExist:
            if user.is_coach or user.is_club:
                default = self.create_default_basic_plan_for_coach_if_not_present()
            else:
                default = self.create_default_basic_plan_if_not_present()
            UserInquiry.objects.create(plan=default, user=user)
            logger.info(f"User {user.id} plan created.")

    def create_default_basic_plan_if_not_present(self):
        """In case when there is no Default plan we would like to create it at first time"""

        args = settings.INQUIRIES_INITAL_PLAN
        try:
            default = InquiryPlan.objects.get(default=True)
        except InquiryPlan.DoesNotExist:
            default = InquiryPlan.objects.create(**args)
        return default

    @staticmethod
    def unseen_requests(queryset, user):
        return queryset.filter(recipient=user, status__in=InquiryRequest.UNSEEN_STATES)

    @staticmethod
    def unseen_user_requests(user):
        return InquiryRequest.objects.filter(
            recipient=user, status=InquiryRequest.STATUS_SENT
        )

    @staticmethod
    def update_requests_with_read_status(queryset, user):
        for request in queryset.filter(status=InquiryRequest.STATUS_SENT):
            if request.recipient == user:
                request.read()
                request.save()
