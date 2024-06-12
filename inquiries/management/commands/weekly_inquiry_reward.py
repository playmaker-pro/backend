from django.core.management.base import BaseCommand

from inquiries.models import InquiryRequest, UserInquiry


class Command(BaseCommand):
    help = "Reward senders with additional inquiry"

    def handle(self, *args, **options) -> None:
        """
        Iterate over all READ inquiries that are older than 7 days
        and reward the sender with one bonus InquiryReqeust.

        Sender can be only rewarded once for the specific unseen inquiry.
        """
        # CASE1
        for inquiry in InquiryRequest.objects.to_notify_sender_about_outdated():
            inquiry.reward_sender()
