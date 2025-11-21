import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from utils.constants import INQUIRY_LIMIT_INCREASE_URL

from .models import InquiryPlan, InquiryRequest, UserInquiry

logger: logging.Logger = logging.getLogger(__name__)
User = get_user_model()


class InquireService:
    @staticmethod
    def get_plan_for_profile_type(profile_type: str, is_premium: bool) -> InquiryPlan:
        """Get appropriate inquiry plan based on profile type and premium status."""
        try:
            if is_premium:
                if profile_type == "PlayerProfile":
                    return InquiryPlan.objects.get(type_ref="PREMIUM_PLAYER")
                else:
                    # All other profiles: Club, Guest, Scout, Coach, Manager, Referee, Other
                    return InquiryPlan.objects.get(type_ref="PREMIUM_STANDARD")
            else:
                if profile_type == "PlayerProfile":
                    return InquiryPlan.objects.get(type_ref="FREEMIUM_PLAYER")
                else:
                    # All other profiles: Club, Guest, Scout, Coach, Manager, Referee, Other
                    return InquiryPlan.objects.get(type_ref="FREEMIUM_STANDARD")
        except InquiryPlan.DoesNotExist:
            # Fallback to basic plan if not found
            logger.warning(f"InquiryPlan not found for {profile_type} (premium={is_premium}). Using basic plan.")
            return InquiryPlan.basic()

    @staticmethod
    def create_basic_inquiry_plan(user) -> None:
        """Create basic inquiry plan for user. Profile-specific plan assignment happens later."""
        plan = InquiryPlan.basic()
        UserInquiry.objects.get_or_create(user=user, defaults={"plan": plan})
        logger.info(f"Created basic plan for {user}")

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
        """Transition inquiries from SENT to RECEIVED status. Only visible inquiries for freemium non-players."""
        sent_requests = queryset.filter(status=InquiryRequest.STATUS_SENT, recipient=user)
        
        if user.is_freemium_non_player:
            # Only transition oldest 5 inquiries to RECEIVED (the visible ones)
            oldest_5_ids = user.inquiry_request_recipient.order_by('created_at')[:5].values_list('id', flat=True)
            for request in sent_requests.filter(id__in=oldest_5_ids):
                request.read()
                request.save()
        else:
            # Transition all to RECEIVED for premium users or players
            for request in sent_requests:
                request.read()
                request.save()

    @staticmethod
    def get_user_sent_inquiries(user: User) -> QuerySet:
        """Get all sent inquiries by user"""
        return user.sender_request_recipient.all().order_by("-created_at")

    @staticmethod
    def get_user_contacts(user: User) -> QuerySet:
        """Get all inquiries contacts by user"""
        return InquiryRequest.objects.contacts(user).order_by("-updated_at")

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
        For received inquiries, it marks them as read by the recipient if they haven't
        been marked as such already. For freemium non-players, only the oldest 5 
        inquiries are marked as read (since they can't see the rest).
        Similarly, for sent inquiries, it marks them as read by the sender.
        """
        if user.is_freemium_non_player:
            # Only mark oldest 5 inquiries as read (the visible ones)
            oldest_5_ids = user.inquiry_request_recipient.order_by('created_at')[:5].values_list('id', flat=True)
            InquiryRequest.objects.filter(
                id__in=oldest_5_ids,
                is_read_by_recipient=False
            ).update(is_read_by_recipient=True)
        else:
            # Mark all received inquiries as read for premium users or players
            InquiryRequest.objects.filter(
                recipient=user, is_read_by_recipient=False
            ).update(is_read_by_recipient=True)

        # Update sent inquiries as read by the sender (no restriction)
        InquiryRequest.objects.filter(sender=user, is_read_by_sender=False).update(
            is_read_by_sender=True
        )

    @staticmethod
    def send_inquiry_limit_reached_email(
        user: settings.AUTH_USER_MODEL, force_send: bool = False
    ) -> None:
        """Send email notification about reaching the limit"""
        if user.userinquiry.can_remind_about_limit or force_send:
            MailingService(
                EmailTemplateRegistry.INQUIRY_LIMIT(
                    context={"url": INQUIRY_LIMIT_INCREASE_URL}
                )
            ).send_mail(user)
